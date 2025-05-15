# version 2.0
# Authors: ChatGPT and Peter Belenko
# python3.11 to support let's encrypt ca
# requirements pip3 install ping3
# requirements pip3 install flask
# requirements pip3 install requests

from flask import Flask, request, jsonify
import re
import requests
import os
import sys
import json
import secrets
import ipaddress
import ping3
import urllib.request as req
from datetime import datetime, timedelta
from urllib.error import HTTPError

# Flask app initialization
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Parse the incoming JSON data
        data = request.get_json()
        if 'message' in data:
            new_message = data['message']

            # Extract data center name from the message text using a regular expression
            data_center_match = re.search(r'\w{3}\d', new_message)
            data_center = data_center_match.group().upper() if data_center_match else "default"
            
            # Process the received message using the MessageHandling class
            message_handler.create_locally_cached_messages(new_message, data_center)

            # Return a success response
            return jsonify({'status': 'success'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_messages', methods=['GET'])
def get_messages():
    # Extract messages and timestamps for response
    messages_by_datacenter = {}
    for data_center, messages in message_handler.short_leave_cache_messages_by_datacenter.items():
        messages_by_datacenter[data_center] = {
            'messages': [msg[0] for msg in messages],
            'timestamps': [timestamp for _, timestamp in messages]
        }

    # Return the messages organized by data center in JSON format
    return jsonify(messages_by_datacenter)


class PagerDuty:
    """
    A class for interacting with the PagerDuty API to trigger and resolve incidents.
    """

    def __init__(self):
        """
        Initialize the PagerDuty class with default values and API endpoints.
        """
        
        # To get a service name for your priority check it here https://developer.pagerduty.com/api-reference/0fa9ad52bf2d2-list-priorities
        # To Test API go to https://developer.pagerduty.com/api-reference/a7d81b0e9200f-create-an-incident
        # Article about priorities https://community.pagerduty.com/forum/t/how-to-set-priority-for-existing-incidents-using-api/1799

        # Predefined PagerDuty API parameters
        self.pd_api = "############"
        self.email = "############"
        self.url = "https://api.pagerduty.com/incidents"

        # PagerDuty IDs for the Priority and Service IDs
        self.p0 = "############"
        self.p1 = "############"
        self.p2 = "############"
        self.p3 = "############"
        self.pagerduty_service_id = "############"
        self.disaster_escalation_policy = "############"
        self.non_disaster_escalation_policy = "############"

    def trigger_pagerduty_incident(self, data_center, title, details, severity, urgency, escalation_policy):
        """
        Trigger a PagerDuty incident.

        Args:
            title (str): The title or description of the incident.
            details (str): Additional details about the incident.
            severity (str): Severity level of the incident ("P0", "P1", "P2", "P3").
            urgency (str): Urgency level of the incident ("low", "high").
            escalation_policy (str): Escalation policy type ("non-disaster" or "disaster").

        Returns:
            tuple: A tuple containing the title and ID of the triggered incident if successful, None otherwise.
        """
        # Map severity levels to PagerDuty incident severity IDs
        if "P0" in severity:
            incident_severity = self.p0
        elif "P1" in severity:
            incident_severity = self.p1
        elif "P2" in severity:
            incident_severity = self.p2
        else:
            incident_severity = self.p3

        # Map escalation policy types to PagerDuty escalation policy IDs
        if "non" in escalation_policy:
            selected_escalation_policy = self.non_disaster_escalation_policy
        elif "disaster" in escalation_policy and not "non" in escalation_policy:
            selected_escalation_policy = self.disaster_escalation_policy
        else:
            selected_escalation_policy = self.non_disaster_escalation_policy

        # Define HTTP headers required for the API request
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'Authorization': f'Token token={self.pd_api}',
            'From': self.email
        }

        # Generate a unique incident key using secrets module
        incident_key = secrets.token_hex(32)

        # Define payload with incident details
        payload = {
            "incident": {
                "type": "incident",
                "title": title,
                "service": {
                    "id": self.pagerduty_service_id,
                    "type": "service_reference"
                },
                "priority": {
                    "id": incident_severity,
                    "type": "priority_reference"
                },
                "urgency": urgency,
                "incident_key": incident_key,
                "body": {
                    "type": "incident_body",
                    "details": details
                },
                "escalation_policy": {
                    "id": selected_escalation_policy,
                    "type": "escalation_policy_reference"
                }
            }
        }

        # Make a POST request to create a PagerDuty incident
        response = requests.post(self.url, headers=headers, data=json.dumps(payload))

        # Check the response status code
        if response.status_code == 201:
            # Extract and print the incident ID if successful
            incident_id = response.json()['incident']['id']
            print(f"PagerDuty incident triggered successfully. Incident ID: {incident_id}")
            return incident_id
        else:
            # Print an error message if the request fails
            description = f"Failed to trigger PagerDuty incident. Status Code: {response.status_code}, Response: {response.text}"
            print(description)

            # Return None in case of failure
            return None


    def resolve_pagerduty_incident(self, incident_id, details=None):
        """
        Resolve a PagerDuty incident.

        Args:
            incident_id (str): The ID of the incident to be resolved.

        Returns:
            None
        """

        if details is None:
            details = "No additional details were provided"

        # Check if incident_id is provided
        if not incident_id:
            print("Incident ID is required to resolve the incident.")
            return
        
        # PagerDuty API endpoint URL for the specified incident_id
        url = f'{self.url}/{incident_id}'

        # Headers for the PagerDuty API request
        headers = {
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'Authorization': f'Token token={self.pd_api}',
            'Content-type': 'application/json',
            'From': self.email
        }

        # Payload to update incident status to "resolved"
        payload = {
            "incident": {
                "type": "incident_reference",
                "status": "resolved",
                "resolution": details
            }
        }

        # Send a PATCH request to update incident status
        response = requests.patch(url, headers=headers, data=json.dumps(payload))
        
        # Check the response status code
        if response.status_code == 200:
            description = f"PagerDuty incident resolved successfully. Incident ID: {incident_id}"
            print(description)
            return True
            
        else:
            # Print error details if resolving the incident fails
            description = f"Failed to resolve PagerDuty incident. Status Code: {response.status_code}, Response: {response.text}"
            print(description)
            return False


class LongtermStorageForActiveIncidents:
    """
    Class for managing long-term storage of active incidents.

    Attributes:
    - script_directory (str): The directory where the script is located.
    - incident_file_path (str): The path to the incident log file.
    """

    def __init__(self):
        # Get the directory where the script is located
        self.script_directory = os.path.dirname(os.path.realpath(__file__))

        # Set the incident log file path in the same directory as the script
        self.incident_file_path = os.path.join(self.script_directory, "incident_log.json")
    

    def find_and_resolve_the_incident(self, active_incidents, incident_id):
        
        """
        Finds and resolves the incident with the given incident_id.

        Args:
            incident_id (int): The ID of the incident to be resolved.

        Returns:
            None
        """

        for data_center, incidents in list(active_incidents.items()):
            messages = incidents.get('messages', [])
            timestamps = incidents.get('timestamps', [])
            
            for i, message in enumerate(messages):
                if message == incident_id:
                    # Remove the message and its corresponding timestamp
                    del messages[i]
                    del timestamps[i]
                    print(f"Removed incident with value {incident_id} from Data Center {data_center}")

            # If there are no more messages for this data center, remove the data center entry
            if not messages:
                del active_incidents[data_center]
                print(f"Removed Data Center {data_center} as it has no more incidents")
            else:
                # Otherwise, update the messages and timestamps for this data center
                incidents['messages'] = messages
                incidents['timestamps'] = timestamps

        # Save the updated incidents back to the file
        if active_incidents:
            storage.save_active_incidents_to_file(active_incidents)
        else:
            # Delete file if nothing to track
            storage.clear_file_content()

        return active_incidents


    def check_existing_data(self):
        """
        Checks if the incident log file exists and returns the previous incidents.

        Returns:
        - previous_incidents (dict): A dictionary containing the previous incidents.
        """
        # Check if the incident log file exists
        if os.path.exists(self.incident_file_path):
            # Check if it's not empty
            if os.path.getsize(self.incident_file_path) == 0:
                previous_incidents = {}
            else:
                # Read existing data from the file
                try:
                    with open(self.incident_file_path, 'r') as file:
                        previous_incidents = json.load(file)

                        # Initialize an empty dictionary for the incident dictionary
                        incidents_dict = {}

                        # Iterate over data centers
                        for data_center, incidents in previous_incidents.items():

                            # Initialize an empty dictionary for the current data center
                            data_center_dict = {}
                            print("Loading active incidents")
                            print(f"Data Center: {data_center}")

                            # Iterate over incidents in the inner dictionary
                            for incident_key, incident_value in incidents.items():

                                # Populate the data center dictionary with incidents
                                data_center_dict[incident_key] = incident_value
                                print(f"Description: {incident_key}, PagerDuty: {incident_value}")

                            # Add the data center dictionary to the result dictionary
                            incidents_dict[data_center] = data_center_dict

                        return(incidents_dict)
                    
                except json.decoder.JSONDecodeError:
                    # Handle the case where the file is empty
                    previous_incidents = {}
                    return(previous_incidents)
        else:
            # Create an empty dictionary if the file doesn't exist yet
            previous_incidents = {}
            return(previous_incidents)


    def log_incident_to_file_and_active_incidents(self, active_incidents, data_center, description, incident_id):
        """
        Log incident information to a local file.

        Args:
            data_center (str): The name of the data center.
            description (str): The title or description of the incident.
            incident_id (str): Incident ID.

        Returns:
            None
        """
        # Check if the incident log file exists
        if os.path.exists(self.incident_file_path):
            # Read existing data from the file
            try:
                with open(self.incident_file_path, 'r') as file:
                    all_incidents = json.load(file)
            except json.decoder.JSONDecodeError:
                # Handle the case where the file is empty
                all_incidents = {}
        else:
            # Create an empty dictionary if the file doesn't exist yet
            all_incidents = {}

        # Check if the data center exists in the dictionary
        if data_center not in all_incidents:
            all_incidents[data_center] = {}

        # Add new incident information to the data center's dictionary
        all_incidents[data_center][description] = incident_id

        # Write the updated dictionary back to the file
        with open(self.incident_file_path, 'w') as file:
            json.dump(all_incidents, file, indent=2)
        
        # Update the active incidents variable
        if data_center in active_incidents:
            active_incidents[data_center][description] = incident_id
        else:
            active_incidents[data_center] = {description: incident_id}
        
        return active_incidents


    def save_active_incidents_to_file(self, incidents):
        # Save the incidents to the file
        with open(self.incident_file_path, 'w') as file:
            json.dump(incidents, file, indent=2)


    def clear_file_content(self):
        """
        Clear the content of a file.

        Returns:
            None
        """
        try:
            # Open the file in write mode to clear its content
            with open(self.incident_file_path, 'w') as file:
                file.truncate(0)  # Truncate the file to size 0
            print(f"Content of the file '{self.incident_file_path}' cleared successfully.")
        except FileNotFoundError:
            print(f"File '{self.incident_file_path}' not found.")
        except Exception as e:
            print(f"An error occurred while clearing the file content: {e}")


class IPAddressProcessing:
    """
    A class for processing IP addresses and IP prefixes.
    """

    @staticmethod
    def check_if_rfc1918_network(prefix):
        """
        Returns True if the network is part of RFC1918.

        Args:
            prefix (str): The IP prefix in CIDR notation.

        Returns:
            bool: True if the network is part of RFC1918, False otherwise.
        """
        return ipaddress.ip_network(prefix).is_private

    @staticmethod
    def ping_ips(ip_list):
        """
        Ping a list of IP addresses and report if they are not pingable.

        Args:
            ip_list (list): List of IP addresses to ping.

        Returns:
            list: List of tuples (ip_address, is_pingable).
        """
        results = []
        for ip in ip_list:
            result = ping3.ping(ip, timeout=1)
            is_pingable = result is not None
            results.append((ip, is_pingable))

        return results

    @staticmethod
    def check_if_rfc1918_address(ip):
        """
        Returns True if the IP address is part of RFC1918.

        Args:
            ip (str): The IP address.

        Returns:
            bool: True if the IP address is part of RFC1918, False otherwise.
        """
        return ipaddress.ip_address(ip.split('/')[0]).is_private

    @staticmethod
    def is_ipv4_address(ip):
        """
        Check if the given string is a valid IPv4 address.

        Args:
            ip (str): The string to check.

        Returns:
            bool: True if the input is a valid IPv4 address, False otherwise.
        """
        try:
            ipaddress.IPv4Address(ip.split('/')[0])
            return True
        except ipaddress.AddressValueError:
            return False

    @staticmethod
    def is_ipv6_address(ip):
        """
        Check if the given string is a valid IPv6 address.

        Args:
            ip (str): The string to check.

        Returns:
            bool: True if the input is a valid IPv6 address, False otherwise.
        """
        try:
            ipaddress.IPv6Address(ip.split('/')[0])
            return True
        except ipaddress.AddressValueError:
            return False

    @staticmethod
    def first_usable_ipv4(prefix):
        """
        Get the first usable IPv4 address in the given prefix.

        Args:
            prefix (str): The IPv4 prefix.

        Returns:
            str: The first usable IPv4 address.
        """
        try:
            network = ipaddress.IPv4Network(prefix, strict=False)
            return str(network.network_address + 1)
        except ipaddress.AddressValueError:
            return None

    @staticmethod
    def is_ip_in_ipv4_prefix(ip, prefix):
        """
        Check if the given IP address belongs to the specified IP prefix.

        Args:
            ip (str): IP address to check.
            prefix (str): IP prefix in CIDR notation.

        Returns:
            bool: True if the IP belongs to the prefix, False otherwise.
        """
        # Convert the IP and prefix strings into ipaddress.IPv4Address and ipaddress.IPv4Network objects
        ip_address = ipaddress.IPv4Address(ip)
        network = ipaddress.IPv4Network(prefix, strict=False)

        # Check if the IP address is within the specified prefix
        return ip_address in network

    @staticmethod
    def is_ip_in_ipv6_prefix(ip, prefix):
        """
        Check if the given IP address belongs to the specified IP prefix.

        Args:
            ip (str): IP address to check.
            prefix (str): IP prefix in CIDR notation.

        Returns:
            bool: True if the IP belongs to the prefix, False otherwise.
        """
        # Convert the IP and prefix strings into ipaddress.IPv6Address and ipaddress.IPv6Network objects
        ip_address = ipaddress.IPv6Address(ip)
        network = ipaddress.IPv6Network(prefix, strict=False)

        # Check if the IP address is within the specified prefix
        return ip_address in network

    @staticmethod
    def is_ipv4_prefix(prefix):
        """
        Check if the given string is a valid IPv4 prefix.

        Args:
            prefix (str): The string to check.

        Returns:
            bool: True if the input is a valid IPv4 prefix, False otherwise.
        """
        try:
            ipaddress.IPv4Network(prefix)
            return True
        except ipaddress.AddressValueError:
            return False
    
    @staticmethod
    def is_ipv6_prefix(prefix):
        """
        Check if the given string is a valid IPv6 prefix.

        Args:
            prefix (str): The string to check.

        Returns:
            bool: True if the input is a valid IPv6 prefix, False otherwise.
        """
        try:
            ipaddress.IPv6Network(prefix, strict=False)
            return True
        except ipaddress.AddressValueError:
            return False

    @staticmethod
    def is_ip_in_ipv4_prefix(ip, prefix):
        """
        Check if the given IP address belongs to the specified IP prefix.

        Args:
            ip (str): IP address to check.
            prefix (str): IP prefix in CIDR notation.

        Returns:
            bool: True if the IP belongs to the prefix, False otherwise.
        """
        # Convert the IP and prefix strings into ipaddress.IPv4Address and ipaddress.IPv4Network objects
        ip_address = ipaddress.IPv4Address(ip)
        network = ipaddress.IPv4Network(prefix, strict=False)

        # Check if the IP address is within the specified prefix
        return ip_address in network


class NetboxRequests:

    def __init__(self):
        """
        Initializes the NetboRequests class.

        The __init__ method sets up the necessary data and variables for the MonitoringBot class.
        It defines the NetBox API URL and token, as well as the GraphQL queries for VLAN groups and IP addresses.
        It also initializes the VLAN group data, addresses data, and timestamp variables.

        If there is no timestamp or VLAN group data available, it triggers a local database update by calling the netbox_graphql function.
        """
        # Define static data for NetBox API
        self.netbox_api_url = 'https://netbox.dev/graphql/'
        self.netbox_api_token = '############'

        # Netbox GraphQL search queries
        self.vlan_group_query = '{ vlan_group_list { name vlans { name prefixes { prefix } } } }'
        self.addresses_query = '{ ip_address_list { address } }'

        self.vlan_group_data = {}
        self.addresses_data = {}
        self.timestamp = datetime.now()

        self.refresh_timer = datetime.now() + timedelta(days=1)

        # Verify if we already have local cache data
        if not self.timestamp or not self.vlan_group_data:
            print("Local DataBase Update is needed. Updating.")
            self.vlan_group_data, self.timestamp, self.refresh_timer = self.netbox_graphql(self.vlan_group_query)
            self.addresses_data, self.timestamp, self.refresh_timer = self.netbox_graphql(self.addresses_query)
            if self.vlan_group_data and  self.addresses_data and self.timestamp and self.refresh_timer:
                pass
            else:
                print("error: Invalid response from NetBox API. Most likely API token is invalid")
                sys.exit()
        else:
            pass

    def netbox_graphql(self, query):
        """
        Perform a GraphQL query to NetBox API.

        Args:
            query (str): GraphQL query string.

        Returns:
            dict: JSON response from the NetBox API.
        """

        # Define NetBox API headers including authorization token
        netbox_api_headers = {"Authorization": f"Token {self.netbox_api_token}"}

        # Make a POST request to NetBox API with the GraphQL query
        result = requests.post(self.netbox_api_url, json={'query': query}, headers=netbox_api_headers)
        
        try:
            # Parse the JSON response
            data = result.json()
        except requests.exceptions.JSONDecodeError:
            print ("error: Invalid response from NetBox API. Most likely API token is invalid")
            return None, None, None

        # Add a timestamp information to later chack if new update is neded or not
        timestamp = datetime.now()

        # Adding a refrash timer
        refrash_timer = timestamp + timedelta(days=1)

        return data, timestamp, refrash_timer

    def get_public_ip_addresses(self, data_center):
        """
        Retrieve public IP addresses associated with a specific data center from NetBox.

        Args:
            data_center (str): The name of the data center.
            vlan_group_data (dict): GraphQL response data for VLAN groups.
            addresses_data (dict): GraphQL response data for IP addresses.
            timestamp (int): The timestamp of the last update.
            refresh_timer (int): The refresh timer threshold.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing lists of active public IPv4 and IPv6 addresses.
        """

        # Check if local database update is needed based on the refresh timer
        if self.timestamp > self.refresh_timer:
            print('Local DataBase Update is needed. Updating.')
            self.vlan_group_data, self.timestamp, self.refresh_timer = self.netbox_graphql(self.vlan_group_query)
            self.addresses_data, self.timestamp, self.refresh_timer = self.netbox_graphql(self.addresses_query)
            if self.vlan_group_data and  self.addresses_data and self.timestamp and self.refresh_timer:
                pass
            else:
                print("error: Invalid response from NetBox API. Most likely API token is invalid")
                sys.exit()
        else:
            pass

        public_prefix_v4 = []  # List to store public IPv4 prefixes
        public_prefix_v6 = []  # List to store public IPv6 prefixes
        public_ipv4_addresses = []  # List to store public IPv4 addresses
        public_ipv6_addresses = []  # List to store public IPv6 addresses
        active_data_center_ipv4_ips = []  # List to store active data center IPv4 addresses
        active_data_center_ipv6_ips = []  # List to store active data center IPv6 addresses
        possible_gateway_ipv4_addresses = [] # List to store passible default gateway IPv4 addresses
        gateway_ipv4_addresses = []  # List to store actual gateway IPv4 addresses

        # Extract public IPv4 and IPv6 prefixes from VLAN group data
        for item in self.vlan_group_data['data']['vlan_group_list']:
            if item['name'] == data_center:
                for vlan in item['vlans']:
                    for net in vlan['prefixes']:
                        if IPAddressProcessing.is_ipv4_prefix(net['prefix']):
                            if not IPAddressProcessing.check_if_rfc1918_network(net['prefix']):
                                public_prefix_v4.append(net['prefix'])
                        elif IPAddressProcessing.is_ipv6_prefix(net['prefix']):
                            if not IPAddressProcessing.check_if_rfc1918_network(net['prefix']):
                                public_prefix_v6.append(net['prefix'])
                        else:
                            pass

        # Extract public IPv4 and IPv6 addresses from IP address data
        for item in self.addresses_data['data']['ip_address_list']:
            if IPAddressProcessing.is_ipv4_address(item['address']):
                if not IPAddressProcessing.check_if_rfc1918_address(item['address']):
                    public_ipv4_addresses.append(item['address'].split('/')[0])
                else:
                    pass
            elif IPAddressProcessing.is_ipv6_address(item['address']):
                if not IPAddressProcessing.check_if_rfc1918_address(item['address']):
                    public_ipv6_addresses.append(item['address'].split('/')[0])
                else:
                    pass
            else:
                pass

        # Find active data center IPv4 addresses within public IPv4 prefixes
        for net_v4 in public_prefix_v4:
            for ip_v4 in public_ipv4_addresses:
                if IPAddressProcessing.is_ip_in_ipv4_prefix(ip_v4, net_v4):
                    active_data_center_ipv4_ips.append(ip_v4)

        # Find active data center IPv6 addresses within public IPv6 prefixes
        for net_v6 in public_prefix_v6:
            for ip_v6 in public_ipv6_addresses:
                if IPAddressProcessing.is_ip_in_ipv6_prefix(ip_v6, net_v6):
                    active_data_center_ipv6_ips.append(ip_v6)

        # Find gateway IPv4 addresses within the data center
        for net_v4 in public_prefix_v4:
            possible_gateway_ipv4_addresses.append(IPAddressProcessing.first_usable_ipv4(net_v4))

        
        # Validate that we do have a default gateway in the possible ipv4 ranges
        for imaginary_ipv4 in possible_gateway_ipv4_addresses:
            for active_ipv4 in list(set(active_data_center_ipv4_ips)):
                if imaginary_ipv4 == active_ipv4:
                    gateway_ipv4_addresses.append(active_ipv4)
        

        return gateway_ipv4_addresses, list(set(active_data_center_ipv4_ips)), list(set(active_data_center_ipv6_ips))


def send_incident_started_to_teams(data_center, description, details, incident_id):
    """
    Sends a notification to the Teams channel indicating that an incident has started.

    Args:
        data_center (str): The data center associated with the incident.
        description (str): The description of the incident.
        details (str): Additional details about the incident.

    Returns:
        None
    """
    send_to_teams_channel(f"An incident has started in Data Center {data_center} with the description:\n {description}.\n Details: {details}\n Link to the Pagerduty: https://pagerduty.com/incidents/{incident_id}")


def send_resolved_to_teams(resolved, incident_id, active_incident_data_center, incident_description):
    """
    Sends a notification to the Teams channel indicating whether an incident has been resolved or not.

    Args:
        resolved (bool): Indicates whether the incident has been resolved in PagerDuty.
        incident_id (str): The ID of the incident.
        active_incident_data_center (str): The data center associated with the incident.
        incident_description (str): The description of the incident.

    Returns:
        None
    """
    if resolved:
        send_to_teams_channel(f"Incident {incident_id} for Data Center {active_incident_data_center} with description:\n {incident_description}\n was resolved")
    else:
        send_to_teams_channel(f"Failed to automatically resolve the incident {incident_id} for Data Center {active_incident_data_center} with description {incident_description}. Please check PagerDuty")
                            

def send_to_teams_channel(message):

    hook_url = 'https://webhook.office.com/webhookb2/15d1f7ea-4c14-4bef-a42c-21878ed0bce2@5e523f03-76f4-4a89-ae97-9aa2208cf15a/IncomingWebhook/437ca57f741f423b937084ed372233f4/b8079b1e-d692-44a8-99f5-2aeb184fabc5' # network-general
    # hook_url = 'https://webhook.office.com/webhookb2/15d1f7ea-4c14-4bef-a42c-21878ed0bce2@5e523f03-76f4-4a89-ae97-9aa2208cf15a/IncomingWebhook/bd5e73aba58a46ea87d138847465862e/e183aa3e-f7cb-473f-bf10-214159ada738' # network-alerts-linux-informational

    message_l = message.splitlines()

    new_message = '<pre>'

    for line in message_l:
        if re.match('\+', line):
            new_message += '<p style="color:#00FF00";>' + line + '</p>'
        elif re.match('\-', line):
            new_message += '<p style="color:#FF0000";>' + line + '</p>'
        else:
            new_message += '<p>' + line + '</p>'

    new_message += '</pre>'

    request = req.Request(url=hook_url, method="POST")
    request.add_header(key="Content-Type", val="application/json")
    data = json.dumps({"text": new_message}).encode()
    try:
        with req.urlopen(url=request, data=data) as response:
            pass
    except HTTPError as e:
        print(f"Failed to send message to Teams channel: {e.reason}")


class MessageHandling:
    def __init__(self, previous_incidents):
        """
        Initializes the MessageHandling class.

        This method sets up the instance variables for the MessageHandling class.
        It initializes the previous_incidents dictionary,
        cache messages dictionaries, vlan_group_data dictionary, addresses_data dictionary,
        timestamp, and refresh_timer.

        Parameters:
            None

        Returns:
            None
        """
        self.short_leave_cache_messages_by_datacenter = {}
        self.long_leave_cache_messages_by_datacenter = {}
        
        # Define the start of the incident
        self.start_of_the_monitoring_server_incident = None
        self.start_of_the_data_center_incident = None

        # check file for previous incidents and validate if file is in a proper format
        if previous_incidents:
            for key, value in previous_incidents.items():
                if not value:
                    del previous_incidents[key]
                if not previous_incidents:
                    # Delete file if nothing to track
                    storage.clear_file_content()
            else:   
                # Update the file with the validated incidents
                storage.save_active_incidents_to_file(previous_incidents)

            # Load previous incidents that were not resolved
            self.active_incidents = previous_incidents
        else:
            self.active_incidents = {}

        # List of the data centers with the incident
        self.data_center_with_the_incident = {}

        # Count of the down devices per data center
        self.down_devices_per_datacenter = {}

        # Count of the recovered devices per data center
        self.recovered_devices_per_datacenter = {}

        # Count of the primary switch down
        self.primary_switch_down = {}
        
        # Count of the primary switch up
        self.primary_switch_up = {}
    
    def resolve_the_incident(self, description, data_center, datacenter_verification=True):
        """
        Resolves the specified incident for the given data center.

        Args:
            description (str): The description of the incident to resolve.
            data_center (str): The data center where the incident occurred.
            datacenter_verification (bool, optional): Flag indicating whether to verify the data center. 
                Defaults to True.

        Returns:
            None
        """
        # Initialize a list to store incidents that need to be resolved
        incidents_to_resolve = []

        # Iterate over incidents in the inner dictionary
        for active_incident_data_center, active_incidents_dict in self.active_incidents.copy().items():
            if datacenter_verification:
                if active_incident_data_center == data_center:
                    for incident_description, active_incident_id in active_incidents_dict.copy().items():
                        if incident_description == description:
                            # Add related incidents to a new variable
                            incidents_to_resolve.append((active_incident_data_center, active_incident_id))

                    updated_incidents = {}
                    temp_incidents = self.active_incidents
                    for active_incident_data_center, incident_id in incidents_to_resolve:
                        print(f"Resolving incident {incident_id} for Data Center {active_incident_data_center}")
                        # Resolve the PagerDuty incident
                        resolved = pagerduty_instance.resolve_pagerduty_incident(incident_id)

                        # Send notification to the Teams channel
                        send_resolved_to_teams(resolved, incident_id, active_incident_data_center, incident_description)

                        resolved_incident = storage.find_and_resolve_the_incident(temp_incidents, incident_id)
                        updated_incidents.update(resolved_incident)

                        if active_incident_data_center in self.primary_switch_down:
                            del self.primary_switch_down[active_incident_data_center]
                        if active_incident_data_center in self.primary_switch_up:
                            del self.primary_switch_up[active_incident_data_center]
                        if active_incident_data_center in self.data_center_with_the_incident:
                            del self.data_center_with_the_incident[active_incident_data_center]
            else:
                for incident_description, active_incident_id in active_incidents_dict.copy().items():
                    if incident_description == description:
                        # Add related incidents to a new variable
                        incidents_to_resolve.append((active_incident_data_center, active_incident_id))

                updated_incidents = {}
                temp_incidents = self.active_incidents
                for active_incident_data_center, incident_id in incidents_to_resolve:
                    print(f"Resolving incident {incident_id} for Data Center {active_incident_data_center}")
                    # Resolve the PagerDuty incident
                    resolved = pagerduty_instance.resolve_pagerduty_incident(incident_id)
                    
                    # Send notification to the Teams channel
                    send_resolved_to_teams(resolved, incident_id, active_incident_data_center, incident_description)

                    resolved_incident = storage.find_and_resolve_the_incident(temp_incidents, incident_id)
                    updated_incidents.update(resolved_incident)

                    if active_incident_data_center in self.primary_switch_down:
                        del self.primary_switch_down[active_incident_data_center]
                    if active_incident_data_center in self.primary_switch_up:
                        del self.primary_switch_up[active_incident_data_center]
                    if active_incident_data_center in self.data_center_with_the_incident:
                        del self.data_center_with_the_incident[active_incident_data_center]

            notification = f'Incident {incident_description} with PagerDuty ID: {active_incident_id} was mitigated.'
            send_to_teams_channel(notification)
            self.active_incidents = updated_incidents

            if self.active_incidents:
                send_to_teams_channel(f'Other incidents that are still active: {self.active_incidents}')

    def create_locally_cached_messages(self, new_message, data_center):
        # Record the time when message was received
        received_time = datetime.now()

        # Set default values for short leave cache if the data center is not present
        self.short_leave_cache_messages_by_datacenter.setdefault(data_center, [])

        # Set default values for long leave cache if the data center is not present
        self.long_leave_cache_messages_by_datacenter.setdefault(data_center, [])

        # Cache the new message along with its timestamp for the specific data center
        self.short_leave_cache_messages_by_datacenter[data_center].append((new_message, received_time.strftime("%Y-%m-%d %H:%M:%S")))

        # Cache the new message along with its timestamp for the specific data center
        self.long_leave_cache_messages_by_datacenter[data_center].append((new_message, received_time.strftime("%Y-%m-%d %H:%M:%S")))

        # Remove messages older than 5 minutes from short leave cache for all data centers
        short_cutoff_time = datetime.now() - timedelta(minutes=5)

        for data_center in list(self.short_leave_cache_messages_by_datacenter.keys()):
            new_messages = []
            for msg, ts in self.short_leave_cache_messages_by_datacenter[data_center]:
                ts_datetime = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                if ts_datetime > short_cutoff_time:
                    new_messages.append((msg, ts))
            if new_messages:
                self.short_leave_cache_messages_by_datacenter[data_center] = new_messages
            else:
                del self.short_leave_cache_messages_by_datacenter[data_center]

        # Remove messages older than 2 days from long leave cache for all data centers
        long_cutoff_time = datetime.now() - timedelta(days=2)

        for data_center in list(self.long_leave_cache_messages_by_datacenter.keys()):
            new_messages = []
            for msg, ts in self.long_leave_cache_messages_by_datacenter[data_center]:
                ts_datetime = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                if ts_datetime > long_cutoff_time:
                    new_messages.append((msg, ts))
            if new_messages:
                self.long_leave_cache_messages_by_datacenter[data_center] = new_messages
            else:
                del self.long_leave_cache_messages_by_datacenter[data_center]

        # Return the locally cached messages
        message_handler.types_of_issues_to_track(data_center, new_message)

    def types_of_issues_to_track(self, data_center, new_message):

        # Conditions:
        #-----------------------------------------------------------------
        # Case Number 1:
        # If we received a lot of messages during the short period of time 
        # from all data centers. Monitoring server is having issues.
        # - Send notification in PagerDuty. 
        # - Send condition cleared.
        #----------------------------------------------------------------

        # Count the number of messages for each data center
        messages_count_by_datacenter = {cached_data_center: len(messages) for cached_data_center, messages in self.short_leave_cache_messages_by_datacenter.items()}

        # Define the incident description
        monitoring_server_description = "Issue with the DCN Network Monitoring server(s)"

        # Retrigger the incident if server was rebooted and we still have active incidents
        if "DCN1" in self.active_incidents and not self.start_of_the_monitoring_server_incident:
            if monitoring_server_description in self.active_incidents["DCN1"]:
                self.start_of_the_monitoring_server_incident = datetime.now()
                print("Retriggering the incident {monitoring_server_description} for Data Center DCN1 from the monitoring server reboot")

        # If the number of data centers is more than 11(librenms APAC has the lowest) and we have more than 40 alerts then notify the PD
        # If there is no active incident for the monitoring server
        if not self.start_of_the_monitoring_server_incident:
            # Check if the number of data centers is more than 11
            # and the total number of alerts is more than 40
            # and we have more than 15 devices down
            if len(messages_count_by_datacenter) > 11 and sum(messages_count_by_datacenter.values()) > 40:
                down_devices = 0
                for cached_data_center, messages in self.short_leave_cache_messages_by_datacenter.items():
                    for data, time in messages:
                        if "Devices up/down" in data and not "recovered from Devices up/down" in data:
                            down_devices += 1

                if  down_devices > 15:

                    # Set incident severity to P2
                    incident_severity = "P2" 

                    urgency = "low"

                    escalation_policy = "non-disaster"
                    
                    # Additional details for the PagerDuty incident
                    details = f"""
                        "Software impacted": "LibreNMS monitoring server",
                        "Data Center(s) impacted": {list(messages_count_by_datacenter.keys())},
                        "Total number of incidents reported during 5 min interval": {sum(messages_count_by_datacenter.values())},
                    """
                    # Record the start time of the incident
                    self.start_of_the_monitoring_server_incident = datetime.now()

                    # Trigger a PagerDuty incident and track its ID
                    incident_id = pagerduty_instance.trigger_pagerduty_incident("DCN1", monitoring_server_description, details, incident_severity, urgency, escalation_policy)
                    
                    # Send notification to the Teams channel
                    send_incident_started_to_teams("DCN1", monitoring_server_description, details, incident_id)

                    # Record the incident in file and active incidents variable
                    refreshed_list_of_incidents = storage.log_incident_to_file_and_active_incidents(self.active_incidents, "DCN1", monitoring_server_description, incident_id)
                    
                    self.active_incidents = refreshed_list_of_incidents

                    # Removing messages from the cache matching devices up/down pattern to prevent from retriggering the incident
                    for key in list(self.short_leave_cache_messages_by_datacenter.keys()):
                            self.short_leave_cache_messages_by_datacenter[key] = [item for item in self.short_leave_cache_messages_by_datacenter[key] if "devices up/down" not in item[0].lower()]
                            # If no messages left, remove the key from the dictionary
                            if not self.short_leave_cache_messages_by_datacenter[key]:
                                del self.short_leave_cache_messages_by_datacenter[key]
                    
                    # Resolve all data center unavailable incidents and wait for the monitoring server to recover
                    if self.data_center_with_the_incident:
                        incidents_to_resolve = []
                        for active_incident_data_center, active_incidents_dict in self.active_incidents.items():
                            for incident_description, active_incident_id in active_incidents_dict.items():
                                if incident_description == f"[{active_incident_data_center}] Data Center Down" or \
                                    incident_description == f"[{active_incident_data_center}] Issue with the Data Center reachability from the monitoring system":
                                    incidents_to_resolve.append((active_incident_data_center, active_incident_id))

                        updated_incidents = {}
                        temp_incidents = self.active_incidents
                        for active_incident_data_center, incident_id in incidents_to_resolve:
                            print(f"Resolving incident {incident_id} for Data Center {active_incident_data_center} with description {incident_description}")
                            # Resolve the PagerDuty incident
                            resolved = pagerduty_instance.resolve_pagerduty_incident(incident_id)
                            
                            # Send notification to the Teams channel
                            send_resolved_to_teams(resolved, incident_id, active_incident_data_center, incident_description)
                            
                            resolved_incident = storage.find_and_resolve_the_incident(temp_incidents, incident_id)
                            updated_incidents.update(resolved_incident)

                            if active_incident_data_center in self.primary_switch_down:
                                del self.primary_switch_down[active_incident_data_center]
                            if active_incident_data_center in self.primary_switch_up:
                                del self.primary_switch_up[active_incident_data_center]
                            if active_incident_data_center in self.data_center_with_the_incident:
                                del self.data_center_with_the_incident[active_incident_data_center]

                        self.active_incidents = updated_incidents

        # If there is an active incident for the monitoring server
        elif self.start_of_the_monitoring_server_incident:
            # If there is an active incident for the monitoring server
            # Check if the number of data centers is more than 11
            # and the total number of alerts is more than 40
            # and we have more than 15 devices recovered
            if len(messages_count_by_datacenter) > 11 and sum(messages_count_by_datacenter.values()) > 40:
                recovered_devices = 0
                for cached_data_center, messages in self.short_leave_cache_messages_by_datacenter.items():
                    for data, time in messages:
                        if "recovered from Devices up/down" in data:
                            recovered_devices += 1

                if  recovered_devices > 15:
                    print(f"Recovered devices: {recovered_devices}")

                    message_handler.resolve_the_incident(monitoring_server_description, "DCN1", False)

        
                    # Removing messages from the cache matching devices up/down pattern to prevent from retriggering the incident
                    for key in list(self.short_leave_cache_messages_by_datacenter.keys()):
                        self.short_leave_cache_messages_by_datacenter[key] = [item for item in self.short_leave_cache_messages_by_datacenter[key] if "devices up/down" not in item[0].lower()]
                        
                        # If no messages left, remove the key from the dictionary
                        if not self.short_leave_cache_messages_by_datacenter[key]:
                            del self.short_leave_cache_messages_by_datacenter[key]
                    

                    # Reset incident tracking variables
                    self.start_of_the_monitoring_server_incident = None
                                                                    
                else:
                    # No need to take action if incident information is incomplete
                    pass
            else:
                pass
        else:
            pass

        #----------------------------------------------------------------------------------
        # Case Number 2:
        # If we received 2 or more messages with device down from the same Data Center. 
        # Data Center can be offline. 
        # - Verify by checking if we received message that sw-01 is down.
        # - Verify by requesting public IP addresses of the network devices from Netbox.
        # - If IP list was received, send ping requests to this public IP.
        # - Include in the results for the PD case. Send the notification in PagerDuty. 
        # - Send condition cleared.
        #---------------------------------------------------------------------------------
        
        # Defining descriptions for the PagerDuty incidents
        data_center_down_description = f"[{data_center}] Data Center Down"
        data_center_unreachable_description = f"[{data_center}] Issue with the Data Center reachability from the monitoring system"

        # Retrigger the incident if server was rebooted and we still have active incidents
        if data_center in self.active_incidents and (not self.data_center_with_the_incident or data_center not in self.data_center_with_the_incident):
            for active_incident_data_center, active_incidents_dict in self.active_incidents.copy().items():
                if data_center_unreachable_description in active_incidents_dict or data_center_down_description in active_incidents_dict:
                    start_of_the_data_center_incident = datetime.now()
                    if data_center not in self.data_center_with_the_incident:
                        self.data_center_with_the_incident[data_center] = {}
                    self.data_center_with_the_incident[data_center]['start_time'] = start_of_the_data_center_incident
        
        # Check if data_center is in short_leave_cache_messages_by_datacenter and we have more than 2 messages
        if not self.start_of_the_monitoring_server_incident:
            if "Devices up/down" in new_message and "recovered from Devices up/down" not in new_message and data_center not in self.data_center_with_the_incident:
                print("maybe here")
                # Count the number of messages for each data center
                for cached_data_center, messages in self.short_leave_cache_messages_by_datacenter.items():
                    # Initialize the count for this data center
                    self.down_devices_per_datacenter[cached_data_center] = 0
                    for data, time in messages:
                        # Check if the substring "Devices up/down" is present in the messages
                        if "Devices up/down" in data and "recovered from Devices up/down" not in data:
                            # Increment the counter if the condition is met
                            self.down_devices_per_datacenter[cached_data_center] += 1
                            if data_center.lower() + "-sw-01" in data:
                                self.primary_switch_down[cached_data_center] = True
                        else:
                            pass
                # Validate if the number of failed devices is greater or equals 3 at the data center and primary switch is down
                for cached_data_center, down_device_count in self.down_devices_per_datacenter.items():
                    if down_device_count >= 3 and cached_data_center in self.primary_switch_down:

                        if cached_data_center not in self.active_incidents:
                            print(f"There are {down_device_count} devices down in {data_center}")
                            
                            # The list to contain information about ping results for the gateways
                            ping_ipv4_gateway_results = []
                           
                           # The list to contain information about ping results for the servers
                            ping_ipv4_servers_results = []

                            # Get a list of public IPv4 addresses for the data center 
                            gateway_ipv4_addresses, all_active_ipv4_addresses, all_active_ipv6_addresses = \
                                netbox.get_public_ip_addresses(data_center)
                            
                            # Ping the list of IPv4 addresses and get results
                            ping_ipv4_gateway = IPAddressProcessing.ping_ips(gateway_ipv4_addresses)

                            for ip, is_pingable in ping_ipv4_gateway:
                                if is_pingable:
                                    ip_results = f"Gateway {ip} is pingable."
                                else:
                                    ip_results = f"Gateway {ip} is not pingable."
                                ping_ipv4_gateway_results.append(ip_results)


                            # Ping the list of IPv4 addresses and get results
                            ping_ipv4_servers = IPAddressProcessing.ping_ips(all_active_ipv4_addresses)

                            for ip, is_pingable in ping_ipv4_servers:
                                if is_pingable:
                                    ip_results = f"IP {ip} is pingable."
                                else:
                                    ip_results = f"IP {ip} is not pingable."
                                ping_ipv4_servers_results.append(ip_results)
                            
                            # Defining the variables
                            pretty_ping_ipv4_gateway_results = ""
                            pretty_ping_ipv4_servers_results = ""

                            # Include ping results in the incident body
                            if ping_ipv4_gateway_results:
                                if "not pingable" in ping_ipv4_gateway_results:
                                    incident_severity = "P0"
                                    urgency = "high"
                                    escalation_policy = "non-disaster"
                                    # Define the incident description
                                    description = data_center_down_description
                                else:
                                    incident_severity = "P2"
                                    urgency = "low"
                                    escalation_policy = "non-disaster"
                                    # Define the incident description
                                    description = data_center_unreachable_description
                                
                                pretty_ping_ipv4_gateway_results = "\n".join(ping_ipv4_gateway_results)
                                
                                if ping_ipv4_servers_results:
                                    pretty_ping_ipv4_servers_results = "\n".join(ping_ipv4_servers_results)
                                else:
                                    pretty_ping_ipv4_servers_results = "Ping Results: Not available"

                            else:
                                pretty_ping_ipv4_gateway_results = "Ping Results: Not available"
                                incident_severity = "P1"
                                urgency = "low"
                                escalation_policy = "non-disaster"
                                description = data_center_down_description

                            # Additional details for the PagerDuty incident
                            details =  f"""
                            Gateway ping results: 
                            {pretty_ping_ipv4_gateway_results},
                            Servers ping results: 
                            {pretty_ping_ipv4_servers_results},
                            """
                            # Record the start time of the incident
                            start_of_the_data_center_incident = datetime.now()

                            # Record the data center name with the incident start time
                            self.data_center_with_the_incident[data_center] = start_of_the_data_center_incident

                            # Trigger a PagerDuty incident and track its ID                      
                            incident_id = pagerduty_instance.trigger_pagerduty_incident(data_center, description, details, incident_severity, urgency, escalation_policy)

                            # Send notification to the Teams channel
                            send_incident_started_to_teams(data_center, description, details, incident_id)

                            # Log incident to a file and update active incidents
                            refreshed_list_of_incidents = storage.log_incident_to_file_and_active_incidents(self.active_incidents, data_center, description, incident_id)

                            # Update the active incidents variable
                            self.active_incidents = refreshed_list_of_incidents

                            # Removing messages from the cache matching devices up/down pattern to prevent from retriggering the incident
                            for key in list(self.short_leave_cache_messages_by_datacenter.keys()):
                                if key == data_center:
                                    self.short_leave_cache_messages_by_datacenter[key] = [item for item in self.short_leave_cache_messages_by_datacenter[key] if "devices up/down" not in item[0].lower()]
                                    # If no messages left, remove the key from the dictionary
                                    if not self.short_leave_cache_messages_by_datacenter[key]:
                                        del self.short_leave_cache_messages_by_datacenter[key]
                    else:
                        pass
            
            # Matching conditions and resolving the incident
            elif data_center in self.data_center_with_the_incident:
                if "recovered from Devices up/down" in new_message:
                     # Count the number of messages for each data center
                    for cached_data_center, messages in self.short_leave_cache_messages_by_datacenter.items():
                        # Initialize the count for this data center
                        self.recovered_devices_per_datacenter[data_center] = 0
                        for data, time in messages:
                            # Check if the substring "Devices up/down" is present in the messages
                            if "Devices up/down" in data and not "recovered from Devices up/down" in data:
                                # Increment the counter if the condition is met
                                self.recovered_devices_per_datacenter[data_center] += 1
                            elif data_center.lower() + "-sw-01" in data:
                                self.primary_switch_up[data_center] = True
                            else:
                                pass
                    if self.primary_switch_up:
                        if data_center in self.primary_switch_up:
                            
                            incidents_to_resolve = []
                            # Iterate over incidents in the inner dictionary
                            for active_incident_data_center, active_incidents_dict in self.active_incidents.copy().items():
                                if active_incident_data_center == data_center:
                                    for incident_description, active_incident_id in active_incidents_dict.copy().items():
                                        if incident_description == data_center_down_description or incident_description == data_center_unreachable_description:
                                        
                                        # Add related incidents to a new variable
                                            incidents_to_resolve.append((active_incident_data_center, active_incident_id))

                                    updated_incidents = {}
                                    temp_incidents = self.active_incidents
                                    for active_incident_data_center, incident_id in incidents_to_resolve:
                                        print(f"Resolving incident {incident_id} for Data Center {active_incident_data_center}")
                                        # Resolve the PagerDuty incident
                                        resolved = pagerduty_instance.resolve_pagerduty_incident(incident_id)

                                        # Send notification to the Teams channel
                                        send_resolved_to_teams(resolved, incident_id, active_incident_data_center, incident_description)

                                        resolved_incident = storage.find_and_resolve_the_incident(temp_incidents, incident_id)
                                        updated_incidents.update(resolved_incident)

                                        if active_incident_data_center in self.primary_switch_down:
                                            del self.primary_switch_down[active_incident_data_center]
                                        if active_incident_data_center in self.primary_switch_up:
                                            del self.primary_switch_up[active_incident_data_center]
                                        if active_incident_data_center in self.data_center_with_the_incident:
                                            del self.data_center_with_the_incident[active_incident_data_center]

                            self.active_incidents = updated_incidents
                                    
                            # Removing messages from the cache matching devices up/down pattern to prevent from retriggering the incident
                            for key in list(self.short_leave_cache_messages_by_datacenter.keys()):
                                if key == data_center:
                                    self.short_leave_cache_messages_by_datacenter[key] = [item for item in self.short_leave_cache_messages_by_datacenter[key] if "devices up/down" not in item[0].lower()]
                                    
                                    # If no messages left, remove the key from the dictionary
                                    if not self.short_leave_cache_messages_by_datacenter[key]:
                                        del self.short_leave_cache_messages_by_datacenter[key]




    # If ISP interface is down, validate?, send to pagerduty, create a message. Send cleared condition to pagerduty.
    # If an interface with ISP wave utilization poped up multiple times during several days. For wave validate through all messages if this is not a duplicate message(from the other side). Report to PagerDuty, create a ticket. Add a marker saying to ignore it, once initial notification was sent out.
    # If wave interface goes down, generate an email, create a PD and a recovery condition
    # If firewall interaface has more than 80% utilization and it's not present in the long cache, create a PagerDuty priority 1 and recovery
    # If IP utilization in Netbox for the range with the roles "* WAN" is over 90% and this message is not in the long term memory, send a PagerDuty (think about recovery condition)
    # If the list of data centers in the same message has 2+ different data centers, select the one that is used in the device name
    # Provide daily incident statistics for EU and US

    
    # # ROUTERS
    # if '-rt-' in new_message:
    #     for cached_message, timestamp in short_leave_cache_messages_by_datacenter[data_center]:
    #         if '-rt-' in new_message and '-rt-' in cached_message:
    #             pass
    #         elif new_message == cached_message:
    #             pass
    #         elif 'Lumen' in cached_message:
    #             pass
    #         else:
    #             pass
    # elif '-ISP-' in new_message:
    #     pass

    # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # description = f"Match found at {current_time}: {new_message} with {cached_message} (Data Center: {data_center})"
    # send_to_teams_channel(description)


if __name__ == '__main__':
    # Instantiate the PagerDuty class
    pagerduty_instance = PagerDuty()

    # Initiate Longterm Storage For Active Incidents
    storage = LongtermStorageForActiveIncidents()

    # Initiate Netbox Requests class
    netbox = NetboxRequests()

    # Check for existing unresolved incidents when the Flask app starts
    previous_incidents = storage.check_existing_data()

    if previous_incidents:
        active_incidents = previous_incidents
    else:
        active_incidents = {}

    # Instantiate the MessageHandling class
    message_handler = MessageHandling(previous_incidents)

    # Application will listen on all local IPs and tcp port 2280
    app.run(host='0.0.0.0', port=2280)
