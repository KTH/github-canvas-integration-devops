#!/usr/bin/python
# -*- coding: utf-8 -*-
# Filename: update_task.py
import json, os, sys
from utils.course import Course
from github import Github
import argparse

# ENVs for updating task
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
CANVAS_COURSE_ID = os.getenv("CANVAS_COURSE_ID")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO_FULLNAME = os.getenv("GH_REPO_FULLNAME")
GITHUB_CONTRIBUTION_PATH = "./contributions"

CANVAS_URL = "https://canvas.kth.se"
github_repo = Github(GH_TOKEN).get_repo(GH_REPO_FULLNAME)
course = Course(CANVAS_URL, CANVAS_TOKEN, CANVAS_COURSE_ID)

# Arguments
MODE = ''
PR_NUMBER = 0
README_SECTIONS = ['']


# Get sub directories of a given path
def get_sub_directory(path):
    categories = dict()

    for dirpath, dirnames, filenames in os.walk(path, topdown=True):
        for category in dirnames:
            categories[category] = {"path": os.path.join(dirpath, category)}
        break

    return categories


# Create new groups and remove deleted groups
def update_groups(canvas_groups_category_id, github_groups):
    groups_canvas = course.list_groups(canvas_groups_category_id)
    print("Canvas groups : " + str(len(groups_canvas)))
    for github_group in github_groups:
        if github_group not in groups_canvas:
            print("Creating group  : " + github_group)
            id_group = course.create_group(canvas_groups_category_id, github_group)
            members = github_group.split("-")
            for member in members:
                print("Adding : " + member)
                id_member = course.get_user_id(member)
                if id_member is None:
                    raise Exception("User {0} not found !".format(member))
                course.add_group_member(id_group, id_member)

    print("Cleaning groups ...")

    deleted_groups = {k: v for k, v in groups_canvas.items() if k not in github_groups}

    for group_name in deleted_groups:
        print("Deleting group : " + group_name)
        r = course.delete_group(deleted_groups[group_name])
        print(r)


# Check if the group is valid
# No same member in same group set
# Member registered in canvas
def check_groups(canvas_groups_category_id, task_name, github_groups):
    groups_canvas = course.list_groups(canvas_groups_category_id)
    registered_user = []
    for group_canvas in groups_canvas:
        members = group_canvas.split("-")
        registered_user += members

    for github_group in github_groups:
        
        if task_name == 'essay' or task_name == 'executable-tutorial' or task_name == 'feedback':
            # check that "task X" is in the README
            fname = github_groups[github_group]["path"] + '/README.md'
            content = open(fname).read().lower()
            
            assert "task 1" in content \
                or "task 2" in content \
                or "task 3" in content , "deadline should be stated exactly as 'task x', eg 'task 1' in " + fname
            
        members = github_group.split("-")
        for member in members:
            if member in registered_user and github_group not in groups_canvas:
                if PR_NUMBER > 0:
                    github_repo.get_pull(PR_NUMBER).create_issue_comment(
                        "Student " + member + " already registered for this task" + "\n\n" +
                        "If not from your group, fetch the upstream.")
                raise Exception("User {0} already registered for {1} !".format(member, task_name))
            id_member = course.get_user_id(member)
            if id_member is None:
                if PR_NUMBER > 0:
                    github_repo.get_pull(PR_NUMBER).create_issue_comment(
                        "Missing student registration :" + member + "\n\n" +
                        "If not from your group, fetch the upstream.")
                raise Exception("User {0} not found !".format(member))
        sections = get_sections(github_groups[github_group]["path"] + '/README.md')
        if not sections == README_SECTIONS:
            if PR_NUMBER > 0:
                github_repo.get_pull(PR_NUMBER).create_issue_comment("Readme is not correctly formatted\n" +
                                                                     "Need exactly: " + str(README_SECTIONS) + "\n\n" +
                                                                     "Got: " + str(sections))
            raise Exception("Readme is not correctly formatted")


# Check if the readme contains the required info
def get_sections(path):
    f = open(path, "r")
    file = f.readlines()
    sections = [s.strip('#').strip() for s in file if s.startswith('#')]
    return sections


# Mapping from github task name to canvas group set id
def task_to_group_category_id(task_name, canvas_groups_set):
    mapping = {
        "course-automation": canvas_groups_set["Course automation"],
        "demo": canvas_groups_set["Demos"],
        "essay": canvas_groups_set["Essays"],
        "executable-tutorial": canvas_groups_set["Executable Tutorials"],
        "feedback": canvas_groups_set["Feedback"],
        "opensource": canvas_groups_set["Open-source contributions"],
        "presentation": canvas_groups_set["Presentations"],
    }
    return mapping.get(task_name, Exception("Groupset mapping"))


# Parse arguments of the script
def parse_args():
    global MODE
    global PR_NUMBER
    global README_SECTIONS

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', dest='mode', type=str, help='Is only check')
    parser.add_argument('--pr', dest='pr', type=int, help='Pull request number', default=0)

    # To handle spaces, use double quote eg. --sections "Assignment Proposal"
    parser.add_argument('--sections', dest='sections', type=str, nargs='+', help='List readme sections',
                        default=['Assignment Proposal', 'Title', 'Names and KTH ID', 'Deadline', 'Category',
                                 'Description'])

    args = parser.parse_args()
    MODE = args.mode
    PR_NUMBER = args.pr
    README_SECTIONS = args.sections


def raise_exception(error):
    if PR_NUMBER > 0:
        github_repo.get_pull(PR_NUMBER).create_issue_comment(error)
    raise Exception(error)


def main():
    parse_args()

    # Get GitHub tasks and canvas group set
    github_tasks = get_sub_directory(GITHUB_CONTRIBUTION_PATH)
    canvas_groups_set = course.get_group_categories()

    for task_name in github_tasks:
        print("Getting tasks : " + task_name)
        github_groups = dict()
        # Get GitHbs groups and check with canvas group set
        canvas_groups_category_id = task_to_group_category_id(task_name, canvas_groups_set)
            
        if task_name == 'presentation' or task_name == 'demo':
            weeks = get_sub_directory(github_tasks[task_name]["path"])
            for week in weeks:
                if not week.startswith('week'):
                    raise_exception("The group folder should be inside a week folder !")
                github_groups.update(get_sub_directory(os.path.join(github_tasks[task_name]["path"], week)))
        else:
            github_groups = get_sub_directory(github_tasks[task_name]["path"])

        check_groups(canvas_groups_category_id, task_name, github_groups)

        # If not check mode, sync the groups with canvas
        if MODE != 'check':
            update_groups(canvas_groups_category_id, github_groups)


main()
