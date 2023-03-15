import json

import requests
from canvasapi import Canvas


def rubric_payload(id, name, description, criterias, assignment_id):
    payload = {'rubric':
                   {"id": id,
                    "title": name,
                    "criteria": {},
                    },
               "rubric_association": {
                   "association_type": "Assignment",
                   "association_id": assignment_id,
                   'purpose': 'grading'
               },
               }

    for i, criteria in enumerate(criterias):
        payload["rubric"]["criteria"][str(i + 1)] = {
            "points": 1,
            "description": criteria['Criteria'],
            "ratings": {}
        }

        for j, option in enumerate(criteria):

            points = 0
            if criteria[option] == 'Yes': points = 1
            if criteria[option] == 'Mandatory': points = 1

            if option != 'Criteria':
                payload["rubric"]["criteria"][str(i + 1)]["ratings"][str(j)] = {
                    "description": criteria[option],
                    "points": points,
                }

    return payload


class Course:
    """
       A class used to wrap api calls to canvas api
       ...
       Attributes
       ----------
       base_url : str
           the base url to the canvas API
       token : str
           the name of the animal
       course_id : int
           course id in canvas
       canvas_course : class
           Class form canvasapi library
       header : int
           header for the call external to the canvasapi library
       """

    def __init__(self, base_url, token, course_id):
        self.base_url = base_url
        self.token = token
        self.course_id = course_id
        self.canvas_course = Canvas(base_url, token).get_course(course_id)
        self.header = {'Authorization': 'Bearer ' + token}

    def get_rubrics(self):
        rubrics = self.canvas_course.get_rubrics()
        return {rubric.title: rubric.id for rubric in rubrics}

    def get_assignments(self):
        assignments = self.canvas_course.get_assignments()
        return {assignment.name: assignment.id for assignment in assignments}

    def get_group_categories(self):
        group_categories = self.canvas_course.get_group_categories()
        return {group_category.name: group_category.id for group_category in group_categories}

    def create_assignment(self, assignment):
        return self.canvas_course.create_assignment(assignment=assignment)

    def update_assignment(self, id, description):
        payload = {'assignment':
            {
                "id": id,
                "description": description
            },
        }
        url = "{0}/api/v1/courses/{1}/assignments/{2}".format(self.base_url, self.course_id, id)
        return requests.put(url, headers=self.header, json=payload)

    def create_group_category(self, name):
        return self.canvas_course.create_group_category(
            name=name)

    def create_rubric(self, title, description, criteria, assignment_id):
        payload = rubric_payload(0, title, description, criteria, assignment_id)
        url = "{0}/api/v1/courses/{1}/rubrics".format(self.base_url, self.course_id)
        r = requests.post(url, headers=self.header, json=payload)

    def update_rubric(self, id, title, description, criteria, assignment_id):
        payload = rubric_payload(id ,title, description, criteria, assignment_id)
        url = "{0}/api/v1/courses/{1}/rubrics/{2}".format(self.base_url, self.course_id, id)
        return requests.put(url, headers=self.header, json=payload)


    def list_groups(self, id_group_category):
        url = "{0}/api/v1/group_categories/{1}/groups?per_page=200".format(self.base_url, id_group_category)
        print(url)
        print(self.header)
        r = requests.get(url, headers=self.header)
        return {group["name"]: group["id"] for group in json.loads(r.content)}


    def create_group(self, id_group_category, name):
        payload = {"group_category_id": id_group_category,
                   "isFull": True,
                   "name": name}
        url = "{0}/api/v1/group_categories/{1}/groups".format(self.base_url, id_group_category)
        r = requests.post(url, headers=self.header, json=payload)
        return json.loads(r.content)["id"]

    def delete_group(self, id_group):
        url = "{0}/api/v1/groups/{1}".format(self.base_url, id_group)
        r = requests.delete(url, headers=self.header)
        return json.loads(r.content)

    def add_group_member(self, id_group_category, id_user):
        payload = {"user_id": id_user}
        url = "{0}/api/v1/groups/{1}/memberships".format(self.base_url, id_group_category)
        print(url)
        return requests.post(url, headers=self.header, data=payload)

    def get_user_id(self, name):
        email = name+"@kth.se"
        paginated_users =  self.canvas_course.get_users(search_term=name)

        for user in paginated_users:
            if user.email == email:
                return user.id

        return None
