
GetNextClassDates = r"""
{
  "operationName": "GetNextClassDates",
  "query": "query GetNextClassDates($university: String!, $campus: String!, $category: String!, $sport: String!) {\n  getNextClassDates(university: $university, campus: $campus, category: $category, sport: $sport)\n}\n",
  "variables": {
    "campus": "%(campus)s",
    "category": "%(category)s",
    "sport": "%(sport)s",
    "university": "%(university)s"
  }
}"""

GetCampusSportClasses = r"""
{
  "operationName": "GetCampusSportClasses",
  "query": "query GetCampusSportClasses($university: String!, $campus: String!, $category: String!, $sport: String!, $date: AWSDate!) {\n  getCampusSportClasses(university: $university, campus: $campus, category: $category, sport: $sport, date: $date) {\n    classId\n    date\n
  "variables": {
    "campus": "%(campus)s",
    "category": "%(category)s",
    "date": "%(date)s",
    "sport": "%(sport)s",
    "university": "%(university)s"
  }
}
"""

BookCampusSportClass = r"""
{
  "operationName": "BookCampusSportClass",
  "query": "mutation BookCampusSportClass($classId: ID!) {\n  bookCampusSportClass(classId: $classId) {\n    classId\n    date\n    startTime\n    endTime\n    name\n    maxParticipants\n    participantsCount\n    isBooked\n    __typename\n  }\n}\n",
  "variables": {
    "classId": "%(classId)s"
  }
}
"""

UnBookCampusSportClass = r"""
{
  "operationName": "UnBookCampusSportClass",
  "query": "mutation UnBookCampusSportClass($classId: ID!) {\n  unbookCampusSportClass(classId: $classId)\n}\n",
  "variables": {
    "classId": "%(classId)s"
  }
}
"""
