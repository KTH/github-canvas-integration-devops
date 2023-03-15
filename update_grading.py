#!/usr/bin/python
# -*- coding: utf-8 -*-
# Filename: update_grading.py
import json
import os, sys, logging
import argparse
from utils.course import Course
from github import Github

# ENVs for updating criteria
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")
CANVAS_COURSE_ID = os.getenv("CANVAS_COURSE_ID")
GH_TOKEN = os.getenv("GH_TOKEN")
GH_REPO_FULLNAME = os.getenv("GH_REPO_FULLNAME")

CANVAS_URL = "https://canvas.kth.se"
github_repo = Github(GH_TOKEN).get_repo(GH_REPO_FULLNAME)
course = Course(CANVAS_URL, CANVAS_TOKEN, CANVAS_COURSE_ID)

# Arguments
ISSUE_ASSIGNEES = ['']
GITHUB_GRADING_PATH = ''
MODE = ''
PR_NUMBER = 0


# Parsing the criteria markdown in GITHUB_GRADING_PATH to a dictionary
# Assignments (sections) are separated by ##
# Description, table and minimum requirements are separated by \n\n\n
def parse_criteria():
    f = open(GITHUB_GRADING_PATH, "r")
    file = f.read()
    sections = file.split("##")
    result = {}

    for section in sections[1:]:
        items = section.split("\n\n\n")
        result[items[0].strip()] = {}
        result[items[0].strip()]['description'] = items[1]
        result[items[0].strip()]['table'] = parse_table(items[2])
        result[items[0].strip()]['grading'] = items[3]
    validate_criteria(result)
    return result


# Parsing a markdown table into a dictionary
def parse_table(table):
    result = []
    header = []

    for n, line in enumerate(table.split('\n')):
        data = {}
        if n == 0:
            header = [t.strip() for t in line.split('|')[1:-1]]
        if n > 1:
            values = [t.strip() for t in line.split('|')[1:-1]]
            for col, value in zip(header, values):
                if col == '':
                    col = 'Criteria'
                data[col] = value
            result.append(data)
    return result


# Validation of the parsed criteria: Tasks, task items, tables items
def validate_criteria(criteria):
    task = [
        "Presentations",
        "Essays",
        "Demos",
        "Open-source contributions",
        "Executable Tutorials",
#        "Course automation",
        "Feedback"
    ]
    task_items = [
        "description",
        "table",
        "grading"
    ]
    table_items = ["Criteria", "Yes", "No"]

    errors = ''

    print("Checking the grading file format...")
    if list(criteria.keys()) != task:
        errors = errors + ("Assignments don't match" + str(task) + '\n\n')

    for task in criteria:
        if list(criteria[task].keys()) != task_items:
            errors = errors + ("Error in : " + task + '\n')
            errors = errors + ("Missing one key " + str(task_items) + '\n\n')
        for table_item in criteria[task]["table"]:
            if list(table_item.keys()) != table_items:
                errors = errors + ("Error in : " + task + '\n')
                errors = errors + ("Missing one key " + str(table_items) + ' for :' + '\n')
                errors = errors + (str(table_item) + '\n\n')

    if errors:
        print(errors)
        github_repo.create_issue("[CANVAS ACTION] Grading file is not correctly formatted", body=errors,
                                 assignees=ISSUE_ASSIGNEES)
        raise Exception("The grading file is not correctly formatted ! ")


# Create or update the rubrics in canvas
def update_rubrics(github_criteria, canvas_rubrics, canvas_assignments):
    for title in github_criteria:

        if title in canvas_rubrics:
            print("Rubric present  " + title)
            course.update_rubric(canvas_rubrics[title], title, github_criteria[title]['description'],
                                 github_criteria[title]['table'],
                                 canvas_assignments[title])
        else:
            print("Rubric missing  " + title)
            course.create_rubric(title, github_criteria[title]['description'], github_criteria[title]['table'],
                                 canvas_assignments[title])


# Create or update the assignments in canvas
def update_assignments(github_criteria, canvas_assignments, canvas_group_set):
    for title in github_criteria:

        if title in canvas_assignments:
            print("Assignments present  " + title)
            course.update_assignment(canvas_assignments[title],
                                     github_criteria[title]['description'])

        else:
            print("Assignments missing  " + title)
            course.create_assignment(
                assignment={
                    "name": title,
                    "submission_types": "none",
                    "notify_of_update": False,
                    "grading_type": "pass_fail",
                    "description": github_criteria[title]['description'],
                    "published": True,
                    "group_category_id": canvas_group_set[title],
                })


# Create or update the group set in canvas
def update_group_set(github_criteria, canvas_group_set):
    for title in github_criteria:

        if title in canvas_group_set:
            print("Groupe set present  " + title)
        else:
            print("Groupe set missing  " + title)
            course.create_group_category(
                name=title
            )


# Parse arguments of the script
def parse_args():
    global GITHUB_GRADING_PATH
    global MODE
    global PR_NUMBER
    global ISSUE_ASSIGNEES

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', dest='mode', type=str, help='Is only check')
    parser.add_argument('--pr', dest='pr', type=int, help='Pull request number', default=0)
    parser.add_argument('--grading', dest='grading_path', type=str, help='Path to the grading criteria',
                        default='./grading-criteria.md')
    parser.add_argument('--issue', dest='issue_assignee', type=str, nargs='+', help='List of issue assignee',
                        default=[''])

    args = parser.parse_args()

    GITHUB_GRADING_PATH = args.grading_path
    MODE = args.mode
    PR_NUMBER = args.pr
    ISSUE_ASSIGNEES = args.issue_assignee


def main():
    parse_args()

    if MODE == 'check':
        print('Check only mode selected,  no update will be made')
        github_criteria = parse_criteria()

    else:
        print('Starting the update...')

        github_criteria = parse_criteria()

        # Sync the group set
        canvas_group_set = course.get_group_categories()
        update_group_set(github_criteria, canvas_group_set)
        canvas_group_set = course.get_group_categories()

        # Sync the assignments
        canvas_assignments = course.get_assignments()
        update_assignments(github_criteria, canvas_assignments, canvas_group_set)
        canvas_assignments = course.get_assignments()

        # Sync the rubrics
        canvas_rubrics = course.get_rubrics()
        update_rubrics(github_criteria, canvas_rubrics, canvas_assignments)


main()
