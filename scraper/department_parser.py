import requests
import json
from tqdm import tqdm
from scraper.utils import save_as_json

class DepartmentDataFetcher:
    """
    A class to fetch and store departmental data from the NIT Jalandhar API.

    The class fetches data for multiple departments and their associated endpoints.
    The fetched data is saved in a JSON file for further use.

    Attributes:
        __departments (dict): A dictionary mapping department names to their respective codes.
        __endpoints (dict): A dictionary mapping endpoint names to their respective API paths.
        __data (dict): A dictionary to store the fetched data for each department.

    Methods:
        fetch_departmental_data():
            Fetches data from the API for each department and endpoint, and saves the data in a JSON file.

    Example:
        fetcher = DepartmentDataFetcher()
        fetcher.fetch_departmental_data()
    """

    def __init__(self):
        """
        Initializes the DepartmentDataFetcher class with department names, endpoint paths,
        and an empty dictionary to store the fetched data.

        The department names and their respective codes, along with the endpoints to be fetched, 
        are hardcoded in the class.
        """

        self.__departments = {
            "Biotechnology": "bt",
            "Chemistry": "cy",
            "Chemical Engineering": "ch",
            "Civil Engineering": "ce",
            "Computer Science and Engineering": "cse",
            "Electronics and Communication Engineering": "ece",
            "Electrical Engineering": "ee",
            "Humanities and Management": "hm",
            "Industrial and Production Engineering": "ipe",
            "Information Technology": "it",
            "Instrumentation and Control Engineering": "ice",
            "Mathematics and Computing": "ma",
            "Mechanical Engineering": "me",
            "Physics": "ph",
            "Textile Technology": "tt"
        }

 
        self.__endpoints = {
            "Message of HOD": "messageofHOD",
            "Achievements": "Achievement",
            "Infrastructure": "Infrastructure?q=Infrastructure",
            "Contact Us": "contactus",
            "Programme Info": "programmeInfo",
            "Academic Coordination": "Acadcord",
            "Syllabus": "Syllabus",
            "Department Calendar": "deptCalendar",
            "Faculty": "Faculty",
            "PhD Scholars": "PhdScholar",
            "Staff": "Staff",
            "Research Area Infrastructure": "Infrastructure?q=Research%20Area",  
            "Department Labs Infrastructure": "Infrastructure?q=Department%20Labs",   
            "Research Labs Infrastructure": "Infrastructure?q=Research%20Labs", 
            "Society and Clubs": "SocietyClubs"
        }

        self.__data = {}
    
    def fetch_departmental_data(self):
        """
        Fetches data for all departments by making API requests for each endpoint.
        The data is stored in a dictionary and saved as a JSON file.

        The method fetches data by iterating through all the departments and endpoints.
        It makes a GET request to the NIT Jalandhar API for each department and each endpoint.
        If the request is successful, the data is stored in a dictionary. If the request fails, 
        an error message is stored. After fetching all data, the dictionary is saved to a JSON file.

        The JSON file is saved in the "jsonfiles" directory with the name "DepartmentalData.json".

        Returns:
            None
        """
        for department_name, dept_code in tqdm(self.__departments.items(), desc="Processing outer loop"):
            department_data = {}
            for endpoint_name, endpoint_path in tqdm(self.__endpoints.items(), desc="Processing inner loop"):
                url = f"https://nitj.ac.in/api/dept/{dept_code}/{endpoint_path}"
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        department_data[endpoint_name] = response.json()
                    else:
                        department_data[endpoint_name] = f"Failed with status code {response.status_code}"
                except requests.exceptions.RequestException as e:
                    department_data[endpoint_name] = f"Error: {e}"
            self.__data[department_name] = department_data
        save_as_json(self.__data, "jsonfiles/DepartmentalData")
        print("Saved the department data as a json file")