"""Agent Resource functions."""

# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Dict, List
import requests
from google.cloud.dialogflowcx_v3beta1 import services
import google.cloud.dialogflowcx_v3beta1.types as types
from google.protobuf import field_mask_pb2

from dfcx_scrapi.core.scrapi_base import ScrapiBase

# logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Agents(ScrapiBase):
    """Core Class for CX Agent Resource functions."""

    def __init__(
        self,
        creds_path: str = None,
        creds_dict: Dict = None,
        creds=None,
        scope=False,
        agent_id: str = None,
    ):
        super().__init__(
            creds_path=creds_path,
            creds_dict=creds_dict,
            creds=creds,
            scope=scope,
        )

        if agent_id:
            self.agent_id = agent_id
            self.client_options = self._set_region(agent_id)

    def list_agents(self, location_id: str) -> List[types.Agent]:
        """Get list of all CX agents in a given GCP project

        Args:
          location_id: The GCP Project/Location ID in the following format
              `projects/<GCP PROJECT ID>/locations/<LOCATION ID>
        Returns:
          agents: List of Agent objects
        """
        request = types.agent.ListAgentsRequest()
        request.parent = location_id

        client_options = self._set_region(location_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )

        response = client.list_agents(request)

        agents = []
        for page in response.pages:
            for agent in page.agents:
                agents.append(agent)

        return agents

    def get_agent(self, agent_id: str) -> types.Agent:
        """Retrieves a single CX agent resource object."""
        request = types.agent.GetAgentRequest()
        request.name = agent_id

        client_options = self._set_region(agent_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )

        response = client.get_agent(request)

        return response

    def create_agent(
        self,
        project_id: str,
        display_name: str,
        gcp_region: str = "global",
        obj: types.Agent = None,
        **kwargs,
    ):
        """Create a Dialogflow CX Agent with given display name.

        By default the CX Agent will be created in the project that the user
        is currently authenticated to
        If the user provides an existing Agent object, create a new CX agent
        based on this object.

        Args:
          project_id: GCP project id where the CX agent will be created
          display_name: Human readable display name for the CX agent
          gcp_region: GCP region to create CX agent. Defaults to 'global'
          obj: (Optional) Agent object to create new agent from

        Returns:
          response
        """

        if obj:
            agent = obj
            parent = "projects/{}/location/{}".format(
                agent.name.split("/")[1], agent.name.split("/")[3]
            )
            agent.display_name = display_name
        else:
            agent = types.agent.Agent()
            parent = "projects/{}/locations/{}".format(project_id, gcp_region)
            agent.display_name = display_name

        agent.default_language_code = "en"
        agent.time_zone = "America/Chicago"

        # set optional args as agent attributes
        for key, value in kwargs.items():
            setattr(agent, key, value)

        client_options = self._set_region(parent)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )
        response = client.create_agent(parent=parent, agent=agent)

        return response


    def validate_agent(
        self,
        agent_id: str = None,
        timeout: float = None) -> Dict:
        """Initiates the Validation of the CX Agent or Flow.

        This function will start the Validation feature for the given Agent
        and then return the results as a Dict.

        Args:
          agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>
          timeout: (Optional) The timeout for this request

        Returns:
          results: Dictionary of Validation results for the entire Agent
            or for the specified Flow.
        """

        if not agent_id:
            agent_id = self.agent_id

        request = types.agent.ValidateAgentRequest()
        request.name = agent_id

        client_options = self._set_region(agent_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )

        response = client.validate_agent(request, timeout=timeout)

        val_dict = self.cx_object_to_dict(response)

        return val_dict


    def get_validation_result(
        self,
        agent_id: str = None,
        timeout: float = None) -> Dict:
        """Extract Validation Results from CX Validation feature.

        This function will get the LATEST validation result run for the given
        CX Agent or CX Flow. If there has been no validation run on the Agent
        or Flow, no result will be returned. Use `dfcx.validate` function to
        run Validation on an Agent/Flow.

        Passing in the Agent ID will provide ALL validation results for
        ALL flows.
        Passing in the Flow ID will provide validation results for only
        that Flow ID.

        Args:
        agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>
        timeout: (Optional) The timeout for this request

        Returns:
        results: Dictionary of Validation results for the entire Agent
            or for the specified Flow.
        """

        if not agent_id:
            agent_id = self.agent_id

        request = types.agent.GetAgentValidationResultRequest()
        request.name = agent_id + "/validationResult"

        client_options = self._set_region(agent_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )

        response = client.get_agent_validation_result(
            request, timeout=timeout
        )

        val_results_dict = self.cx_object_to_dict(response)

        return val_results_dict


    def export_agent(self, agent_id: str, gcs_bucket_uri: str) -> str:
        """Exports the specified CX agent to Google Cloud Storage bucket.

        Args:
          agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>
          gcs_bucket_uri: The Google Cloud Storage bucket/filepath to export the
            agent to in the following format:
              `gs://<bucket-name>/<object-name>`

        Returns:
          response: A Long Running Operation (LRO) ID that can be used to
            check the status of the export using dfcx.get_lro()
        """

        request = types.agent.ExportAgentRequest()
        request.name = agent_id
        request.agent_uri = gcs_bucket_uri

        client_options = self._set_region(agent_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )
        response = client.export_agent(request)

        return response.operation.name


    def restore_agent(self, agent_id: str, gcs_bucket_uri: str) -> str:
        """Restores a CX agent from a gcs_bucket location.
        Currently there is no way to restore back to default
        settings via the api. The feature request for this is logged.

        Args:
          agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>
          gcs_bucket_uri: The Google Cloud Storage bucket/filepath to export the
            agent to in the following format:
              `gs://<bucket-name>/<object-name>`

        Returns:
          response: A Long Running Operation (LRO) ID that can be used to
            check the status of the import using dfcx.get_lro()
        """

        request = types.RestoreAgentRequest()
        request.name = agent_id
        request.agent_uri = gcs_bucket_uri

        client_options = self._set_region(agent_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )
        response = client.restore_agent(request)

        return response.operation.name

    def update_agent(
        self, agent_id: str, obj: types.Agent = None, **kwargs
    ) -> types.Agent:
        """Updates a single Agent object based on provided kwargs.

        Args:
          agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>
          obj: (Optional) The CX Agent object in proper format. This can also
              be extracted by using the get_agent() method.
        """

        if obj:
            agent = obj
            agent.name = agent_id
        else:
            agent = self.get_agent(agent_id)

        # set agent attributes to args
        for key, value in kwargs.items():
            setattr(agent, key, value)
        paths = kwargs.keys()
        mask = field_mask_pb2.FieldMask(paths=paths)

        client_options = self._set_region(agent_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )
        response = client.update_agent(agent=agent, update_mask=mask)

        return response

    def delete_agent(self, agent_id: str) -> str:
        """Deletes the specified Dialogflow CX Agent.

        Args:
          agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>
        """
        client_options = self._set_region(agent_id)
        client = services.agents.AgentsClient(
            credentials=self.creds, client_options=client_options
        )
        client.delete_agent(name=agent_id)

        return "Agent '{}' successfully deleted.".format(agent_id)


    def validate_agent_rest(self, agent_id: str) -> Dict:
        """Initiates the Validation of the CX Agent or Flow.
        *NOTE* THIS METHOD IS BEING DEPRECATED SOON (8/15/21)

        This function will start the Validation feature for the given Agent
        and then return the results as a Dict.

        Args:
        agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>

        Returns:
        results: Dictionary of Validation results for the entire Agent
            or for the specified Flow.
        """
        location = agent_id.split("/")[3]
        if location != "global":
            base_url = "https://{}-dialogflow.googleapis.com/v3beta1".format(
                location
            )
        else:
            base_url = "https://dialogflow.googleapis.com/v3beta1"

        url = "{0}/{1}/validationResult".format(base_url, agent_id)
        headers = {"Authorization": "Bearer {}".format(self.token)}

        # Make REST call
        results = requests.get(url, headers=headers)
        results.raise_for_status()

        return results.json()


    def get_validation_result_rest(
        self,
        agent_id: str,
        flow_id: str = None) -> Dict:
        """Extract Validation Results from CX Validation feature.
         *NOTE* THIS METHOD IS BEING DEPRECATED SOON (8/15/21)

        This function will get the LATEST validation result run for the given
        CX Agent or CX Flow. If there has been no validation run on the Agent
        or Flow, no result will be returned. Use `dfcx.validate` function to
        run Validation on an Agent/Flow.

        Passing in the Agent ID will provide ALL validation results for
        ALL flows.
        Passing in the Flow ID will provide validation results for only
        that Flow ID.

        Args:
          agent_id: CX Agent ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>
          flow_id: (Optional) CX Flow ID string in the following format
            projects/<PROJECT ID>/locations/<LOCATION ID>/agents/<AGENT ID>/
              flows/<FLOW ID>

        Returns:
          results: Dictionary of Validation results for the entire Agent
            or for the specified Flow.
        """

        if flow_id:
            location = flow_id.split("/")[3]
            if location != "global":
                base_url = (
                    "https://{}-dialogflow.googleapis.com/v3beta1".format(
                        location
                    )
                )
            else:
                base_url = "https://dialogflow.googleapis.com/v3beta1"

            url = "{0}/{1}/validationResult".format(base_url, flow_id)
        else:
            location = agent_id.split("/")[3]
            if location != "global":
                base_url = (
                    "https://{}-dialogflow.googleapis.com/v3beta1".format(
                        location
                    )
                )
            else:
                base_url = "https://dialogflow.googleapis.com/v3beta1"

            url = "{0}/{1}/validationResult".format(base_url, agent_id)

        headers = {"Authorization": "Bearer {}".format(self.token)}

        # Make REST call
        results = requests.get(url, headers=headers)
        results.raise_for_status()

        return results.json()
