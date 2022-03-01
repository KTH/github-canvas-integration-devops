# GitHub Canvas Integration

## About it

This tools was created for the course [DD2482 Automated Software Testing and DevOps](https://www.kth.se/student/kurser/kurs/DD2482?l=en) at KTH and is meant to create an interface between the course [GitHub repository](https://github.com/KTH/devops-course) and the Canvas.

For educational purpose, all the assignments registration are done on GitHub. And the goal of this tool is to replicate and keep up to date all the assignment and groups with Canvas.

## Requirements

In the GitHub secrets, you need to add the following :

- CANVAS_TOKEN
- CANVAS_COURSE_ID

corresponding to the Canvas access token generated [on your profile](https://canvas.kth.se/profile/settings), and the course id of the Canvas course.

## How it works

- **Update grading**
    
The GitHub action `update_criteria.yml` is triggered each time the `grading-criteria.md` is changed. We are first parsing the file to extract the assignments and then using the Canvas API to create/update the following :

    - Group categories sets
    - Assignements
    - Rubrics
 
 - **Update task**
    
The GitHub action `update_task.yml` is triggered each time the a change is made in the contributions folder. We are first getting the task present in the contributions folder and then using the Canvas API to manage the group category by adding/removing the following :

    - Group
    - Members 

## How to run

`python3 ./update_task.py`

`python3 ./update_grading.py`

