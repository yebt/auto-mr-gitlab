#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import requests
import datetime
import argparse
from typing import Dict, List, Tuple
from dotenv import load_dotenv


class GitlabReleaseManager:

    def __init__(
        self, token: str, project_id, api_url: str = "https://gitlab.com/api/v4"
    ) -> None:
        self.token = token
        self.project_id = project_id
        self.api_url = api_url
        self.headers = {"PRIVATE-TOKEN": token}

    def get_latest_tag(self) -> str:
        """Get latest tag from the repo"""
        url = f"{self.api_url}/projects/{self.project_id}/repository/tags"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f"Error getting the tag: {response.text}")
            sys.exit(1)

        tags = response.json()
        if not tags:
            return "v0.0.0"  # default tag

        return tags[0]["name"]


if __name__ == "__main__":
    load_dotenv()
    env_token = os.getenv("GITLAB_ACCESS_TOKEN")
    env_project = os.getenv("GITLAB_PROJECT_ID")

    parser = argparse.ArgumentParser(description="Automatization MR")
    parser.add_argument(
        "--token",
        required=env_token == None,
        default=os.getenv("GITLAB_ACCESS_TOKEN"),
        help="GitLab Personal Access Token",
    )

    parser.add_argument(
        "--project",
        required=env_project == None,
        default=os.getenv("GITLAB_PROJECT_ID"),
        help="GitLab Project ID",
    )

    parser.add_argument(
        "--api", default="https://gitlab.com/api/v4", help="URL de la API de GitLab"
    )

    args = parser.parse_args()
    print("__")
