# GitHub Canvas Integration

## About it

This tools was created for the course [DD2482 Automated Software Testing and DevOps](https://www.kth.se/student/kurser/kurs/DD2482?l=en) at KTH and is meant to create an interface between the course [GitHub repository](https://github.com/KTH/devops-course) and the Canvas.

For educational purpose, all the assignments registration are done on GitHub. And the goal of this tool is to replicate and keep up to date all the assignment and groups with Canvas.

## Requirements

In the GitHub secrets, you need to add the following :

| key | Details  | 
|---|---|
| CANVAS_TOKEN |  Canvas access token generated [on your profile](https://canvas.kth.se/profile/settings) |
| CANVAS_COURSE_ID | Course ID of the Canvas course  | 
| GH_REPO_FULLNAME  | Full name of the repo using running the code (e.g. KTH/devops-course)  | 
| GH_TOKEN  |  GitHub access token generated [on your profile](https://github.com/settings/tokens) | 

- The *CANVAS_* secrets are used to interact with the canvas server (e.g. manage assignments, groups, ...)
- The *GH_* secrets are used to interact with h the GitHub repo (e.g. open issue, comment PR, ..)

## How it works

- **Update grading**
    
The GitHub action `update_criteria.yml` is triggered each time the `grading-criteria.md` is changed. We are first parsing the file to extract the assignments, then we validate the structure, and finally we use the Canvas API to create/update the following :

    - Group categories sets
    - Assignements
    - Rubrics
    
 
 - **Update task**
    
The GitHub action `update_task.yml` is triggered each time a change is made in the contributions folder. We are first getting the task present in the contributions folder and then using the Canvas API to manage the group category by adding/removing the following :

    - Group
    - Members 
    
 While validating the group, we check the following:
 
 - Members can't be registered more than one time for a task
 - Members must be registered to the canvas course
 - README.md must have the correct sections

## How to run

`python3 ./update_task.py`

`python3 ./update_grading.py`

## Options

All options have a default value and can be adapted using the following:

| Option | Usage | Example | update_grading.py | update_task.py |
|---|---|---|---|---|
|--mode| If you only want to check the requirements  | `./update_task.py --mode check` |:heavy_check_mark:|:heavy_check_mark:|
|--pr| Pull request id | `./update_task.py -pr ${{github.event.number}}` |:x:|:heavy_check_mark:|
|--sections| Sections required in the proposal | `./update_task.py --sections "Assignment Proposal" Deadline` |:x: |:heavy_check_mark:|
|--grading| Path to grading criterias | `./update_grading.py --grading ./grading-criteria-md` |:heavy_check_mark:|:x:|
|--issue| List of issue assignees | `./update_grading.py --issue githubuser1 ${{github.actor}}` |:heavy_check_mark:|:x:|

