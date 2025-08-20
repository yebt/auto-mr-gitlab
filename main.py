#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import requests
import datetime
import argparse
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv
from halo import Halo


class Alert:

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    ORANGE = "\033[38;5;166m"
    PURPLE = "\033[38;5;201m"

    @staticmethod
    def info(msg: str, additional: str = "", padding: int = 0):
        if additional:
            additional = f"{Alert.WARNING}{additional}{Alert.ENDC}"

        prefix = f"{Alert.OKBLUE}{Alert.BOLD}[{Alert.ENDC}{Alert.BOLD}>>{Alert.OKBLUE}{Alert.BOLD}] "
        if padding > 0:
            print(" " * padding, end="")
            prefix = f"{Alert.PURPLE}{Alert.BOLD}~~ "

        print(f"{prefix}{Alert.ENDC}{Alert.OKBLUE}{msg}{Alert.ENDC}  {additional}")

    @staticmethod
    def error(msg: str, additional: str = ""):
        if additional:
            additional = f"{Alert.WARNING}{additional}{Alert.ENDC}"

        print(
            f"{Alert.FAIL}{Alert.BOLD}[{Alert.ENDC}{Alert.BOLD}!!{Alert.FAIL}{Alert.BOLD}] {Alert.ENDC}{Alert.FAIL}{msg}{Alert.ENDC}  {additional}"
        )

    @staticmethod
    def success(msg: str, additional: str = ""):
        if additional:
            additional = f"{Alert.WARNING}{additional}{Alert.ENDC}"

        print(
            f"{Alert.OKGREEN}{Alert.BOLD}[{Alert.ENDC}{Alert.BOLD}√√{Alert.OKGREEN}{Alert.BOLD}] {Alert.ENDC}{Alert.OKGREEN}{msg}{Alert.ENDC}  {additional}"
        )

    @staticmethod
    def warning(msg: str, additional: str = ""):
        if additional:
            additional = f"{Alert.OKCYAN}{additional}{Alert.ENDC}"

        print(
            f"{Alert.WARNING}{Alert.BOLD}[{Alert.ENDC}{Alert.BOLD}??{Alert.WARNING}{Alert.BOLD}] {Alert.ENDC}{Alert.WARNING}{msg}{Alert.ENDC}  {additional}"
        )

    @staticmethod
    def header(msg: str):
        print()
        print(f"{Alert.HEADER}{Alert.BOLD}{Alert.UNDERLINE}{msg}{Alert.ENDC}")
        print()

    @staticmethod
    def print_header():
        header = [
            "",
            "   JJ          JJ   ",
            "  JJJ          JJC  ",
            "  JCJJ        JJJJ  ",
            " JJJJJJ      UJCJJJ ",
            "}}rxrxrJJJJJJxrrxr}}",
            "}}}{rrxcJJJJzrxr{}}}",
            " }}}}rrxJJCJrrr}}}[ ",
            "   [}}jrnJJxxj}}[   ",
            "      }}rXXx}}      ",
            "        [tj[        ",
        ]
        print("\n\t\033[38;5;166m".join(header))
        print("\033[0m")


class GitlabReleaseManager:

    def __init__(
        self,
        token: str,
        project_id,
        api_url: str = "https://gitlab.com/api/v4",
        source_branch: str = "development",
        target_branch: str = "main",
    ) -> None:
        self.token = token
        self.project_id = project_id
        self.api_url = api_url
        self.headers = {"PRIVATE-TOKEN": token}
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.emoji = "no_mouth"
        self.emojis = ["no_mouth", "thumbsup"]

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

    def _get_commit_date(self, ref: str) -> str:
        """Get the date of a commit or tag"""
        url = f"{self.api_url}/projects/{self.project_id}/repository/commits/{ref}"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"Error getting info of an commit: {response.text}")
            sys.exit(1)

        return response.json()["created_at"]

    def count_commits_by_type(
        self, from_commit: str, to_branch: str = "development"
    ) -> Dict[str, int]:
        """count commits by type"""
        url = f"{self.api_url}/projects/{self.project_id}/repository/commits"
        params = {"ref_name": to_branch, "since": self._get_commit_date(from_commit)}

        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            print(f"Error getting commits: {response.text}")
            sys.exit(1)

        commits = response.json()

        # TODO: add support to map breaking changes to map a major version
        # Count the commit
        counts = {"fix": 0, "feat": 0}
        for commit in commits:
            message = str(commit["title"]).lower()
            if "feat:" in message:
                counts["feat"] += 1
                counts["fix"] = 1  # reset the count in the starter
            else:
                # Take like a fix
                counts["fix"] += 1

        return counts

    def generate_new_tag(self, last_tag: str, commit_counts: Dict[str, int]) -> str:
        """
        Generate new tag based in the last tag and the count in the changes
        - feats
        - fixes
        """
        match = re.match(r"v(\d+)\.(\d+)\.(\d+)", last_tag)
        if not match:
            print(f"Error: bad format in tag: {last_tag}")
            sys.exit(1)
        major, minor, patch = map(int, match.groups())

        # TODO: add support to map breaking changes to map a major version
        # Applay semantic versioning

        if commit_counts["feat"] > 0:
            minor += commit_counts["feat"]
            if commit_counts["fix"] > 0:
                patch = commit_counts["fix"]
        elif commit_counts["fix"] > 0:
            patch += commit_counts["fix"]
        else:
            patch = 1

        return f"v{major}.{minor}.{patch}"

    @Halo(text="Createing MR", spinner="dots3")
    def create_merge_request(
        self, source_branch: str, target_branch: str, title: str
    ) -> int:
        """Create a merge request and return the id"""
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests"
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch": False,
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code not in [200, 201]:
            Alert.error(f"Error cerating a merge request: {response.text}")
            sys.exit(1)

        iid = response.json()["iid"]
        return iid

    @Halo(text="Approving", spinner="dots3")
    def approve_merge_request(self, mr_id: int) -> bool:
        """Approvate the merge request generated"""
        url = (
            f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_id}/approve"
        )
        response = requests.post(url, headers=self.headers)

        # Add emojii
        for emojiName in self.emojis:
            url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_id}/award_emoji?name={emojiName}"
            requests.post(url, headers=self.headers)

        if response.status_code not in [200, 201]:
            print(f"Error in the approve of merge request: {response.text}")
            return False

        return True

    @Halo(text="Checking status", spinner="dots3")
    def check_for_conflicts(self, mr_id: int) -> Dict[str, Any]:
        """Verificate if exists conflicts"""
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_id}"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"Error getting mr info: {response.text}")
            sys.exit(1)

        data = response.json()

        # return {
        #     "has_conflicts": data["has_conflicts"],
        #     "changes_count": data["changes_count"],
        #     "merge_status": data["merge_status"],
        # }
        return data

    @Halo(text="Merging", spinner="dots3")
    def merge_mr(self, mr_id: int) -> bool:
        """Merge MR"""
        url = f"{self.api_url}/projects/{self.project_id}/merge_requests/{mr_id}/merge"
        response = requests.put(url, headers=self.headers)
        if response.status_code not in [200, 201]:
            print(f"Error merging MR: {response.text}")
            return False
        return True

    @Halo(text="Creating Tag", spinner="dots3")
    def create_tag(self, tag_name: str, ref: str) -> bool:
        """Creating a tag in the repo"""
        url = f"{self.api_url}/projects/{self.project_id}/repository/tags"

        data = {"tag_name": tag_name, "ref": ref}

        response = requests.post(url, headers=self.headers, json=data)

        if response.status_code not in [200, 201]:
            print(f"Error creating a tag: {response.text}")
            return False

        return True

    def run_release_proccess(self):
        """Execute all"""

        skip = False

        Alert.info("Initializing")

        # [√√] Last tag:  v2.18.6
        # [√√] Commits found:  {'fix': 8, 'feat': 4}
        # [√√] New tag generated  v2.22.8
        # [√√] New MR title generated:  Main Release: 28.04.2025 TAG: v2.22.8

        # 1. Getting last tag
        if skip:
            last_tag = "v2.18."
        else:
            last_tag = self.get_latest_tag()
        Alert.success(f"Last tag:", last_tag)

        # 2. Count commits
        if skip:
            commit_counts = {"fix": 8, "feat": 4}
        else:
            commit_counts = self.count_commits_by_type(last_tag)
        Alert.success(f"Commits found:", str(commit_counts))

        # 3. Make new tag just the string
        if skip:
            new_tag = "v2.22.8"
        else:
            new_tag = self.generate_new_tag(last_tag, commit_counts)
        Alert.success(f"New tag generated", new_tag)

        # 4 Make new title, just string
        if skip:
            mr_title = "Main Release: 28.04.2025 TAG: v2.22.8"
        else:
            today = datetime.datetime.now().strftime("%d.%m.%Y")
            mr_title = f"Main Release: {today} TAG: {new_tag}"
        Alert.success("New MR title generated:", mr_title)

        # 5. Create MR from development to main
        Alert.info("Crating MR")
        if skip:
            spinner = Halo(text="Creating", spinner="dots4")
            spinner.start()
            time.sleep(1)
            spinner.succeed()
            spinner.stop()
            mr_id = 186
        else:
            mr_id = self.create_merge_request(
                self.source_branch, self.target_branch, mr_title
            )
        Alert.success("Merge request created:", str(mr_id))

        # 6. check conflicts
        Alert.info("Checking status")
        mr_state = None
        while True:
            mr_state = self.check_for_conflicts(mr_id)
            if mr_state["prepared_at"]:
                break
        has_conflicts = mr_state["has_conflicts"]
        Alert.info("Has conflicts:", mr_state["has_conflicts"], 2)
        Alert.info("Changes:", mr_state["changes_count"], 2)
        Alert.info("Prepared:", mr_state["prepared_at"], 2)
        Alert.info("Status:", mr_state["merge_status"], 2)
        Alert.info("State:", mr_state["state"], 2)
        Alert.info("Web URL:", mr_state["web_url"], 2)

        if has_conflicts:
            Alert.error("Merge request has conflicts")
            sys.exit(1)

        Alert.info("Aprovating MR")
        if not skip:
            rslt = self.approve_merge_request(mr_id)
            if not rslt:
                Alert.error("MR not approved")
                sys.exit(1)
        Alert.success("Aproved")

        Alert.info("Mergin MR")
        if not skip:
            rslt = self.merge_mr(mr_id)
            if not rslt:
                Alert.error("MR not merged")
                sys.exit(1)
        Alert.success("Merged")

        Alert.info("Waiting for complete merge proccess")

        spinnerc = Halo("Waiting for merge proccess", spinner="dots")
        spinnerc.start()
        while True:
            time.sleep(3)  # checking each 3 second
            merge_request = self.check_for_conflicts(mr_id)
            if merge_request["state"] == "merged":
                break
            Alert.info("waiting")
        spinnerc.succeed("Merged")
        spinnerc.stop()

        Alert.info("Creating new TAG")
        if not skip:
            rslt = self.create_tag(new_tag, "main")
            if not rslt:
                Alert.error("Tag not created")
                sys.exit(1)
        Alert.success("Tag created")

        Alert.header("Ready to deploy 🚀")


if __name__ == "__main__":

    Alert.print_header()

    Alert.header("# Initializing proccess:")

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

    parser.add_argument(
        "--source_branch",
        default="development",
        help="Branch of origin, from wich the request originates",
    )

    parser.add_argument(
        "--target_branch",
        default="main",
        help="Branch of destination, where the merger application will apply",
    )
    args = parser.parse_args()
    release_manager = GitlabReleaseManager(
        args.token,
        args.project,
        args.api,
        args.source_branch,
        args.target_branch,
    )
    release_manager.run_release_proccess()

    # # try:
    # #     release_manager = GitlabReleaseManager(args.token, args.project, args.api)
    # #     release_manager.run_release_proccess()
    # # except Exception as e:
    # #     print(f"Error in usage: {e}")
    # #     raise e
    # #     sys.exit(1)
