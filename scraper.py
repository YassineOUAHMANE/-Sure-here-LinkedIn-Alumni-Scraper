import pandas as pd 
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


path = "C:/Users/YASSINE/Desktop/chrome-win64/chrome-win64/chrome_proxy.exe"
# download the chromedriver.exe from https://chromedriver.storage.googleapis.com/index.html?path=106.0.5249.21/

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("executable_path=" + path)
driver = webdriver.Chrome(options=chrome_options)

# Login
def login():
    # Charger les informations d'identification depuis le fichier
    with open("C:/Users/YASSINE/Desktop/Mon portfolio/Project/Projet Python/login.txt") as login_file:
        lines = login_file.readlines()
        email = lines[0].strip()
        password = lines[1].strip()

    driver.get("https://www.linkedin.com/login")
    
    # Attendez que les champs de connexion soient présents dans le DOM
    eml = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
    passwd = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password")))
    
    # Remplissez les champs et cliquez sur le bouton de connexion
    eml.send_keys(email)
    passwd.send_keys(password)
    
    # Utilisez une attente explicite pour attendre que le bouton soit présent
    login_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "login__form_action_container ")))
    
    # Cliquez sur le bouton de connexion
    login_button.click()
    
    # Ajoutez un délai facultatif pour vous assurer que la page a le temps de se charger
    time.sleep(3)


# Return all profiles urls of M&A employees of a certain company
def getProfileURLs(companyName):
    time.sleep(1)
    driver.get("https://www.linkedin.com/company/" + companyName + "/people/?keywords=M%26A%2CMergers%2CAcquisitions")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    source = BeautifulSoup(driver.page_source)
    visibleEmployeesList = []
    
    
    visibleEmployees = source.find_all('a', {"class":'app-aware-link'})
    for profile in visibleEmployees:
        if profile.get('href').split('/')[3] ==  'in':
            visibleEmployeesList.append(profile.get('href'))
    invisibleEmployeeList = []
    invisibleEmployees = source.find_all('div', {"class":'artdeco-entity-lockup artdeco-entity-lockup--stacked-center artdeco-entity-lockup--size-7 ember-view'})
    for invisibleguy in invisibleEmployees:
        try:
         title = invisibleguy.findNext('div', {'class':'lt-line-clamp lt-line-clamp--multi-line ember-view'}).contents[0].strip('\n').strip('  ')
        except:
           continue    
        invisibleEmployeeList.append(title)
        # A profile can either be visible or invisible
        profilepiclink = ""
        visibleProfilepiclink = invisibleguy.find('img', {'class':'lazy-image ember-view'})
        invisibleProfilepicLink = invisibleguy.find('img', {'class':'lazy-image ghost-person ember-view'})
        if visibleProfilepiclink == None:
            profilepiclink = invisibleProfilepicLink.get('src')
        else:
            profilepiclink = visibleProfilepiclink.get('src')
        if profilepiclink not in invisibleEmployees:
            invisibleEmployeeList.append(profilepiclink)
    return (visibleEmployeesList[5:], invisibleEmployeeList)
#Testing spreadsheet of urls
profilesToSearch = pd.DataFrame(columns=["ProfileID", "Title", "ProfilePicLink"])
company = 'apple'
searchable = getProfileURLs(company)
#
for profileId in searchable[0]:
     profilesToSearch.loc[len(profilesToSearch.index)] = [profileId, "", ""]
for i in range(0, len(searchable[1]), 2):
     profilesToSearch.loc[len(profilesToSearch.index)] = ["", searchable[1][i], searchable[1][i+1]]
profilesToSearch     
# parses a type 2 job row
def parseType2Jobs(alltext):
    jobgroups = []
    company = alltext[16][:len(alltext[16]) // 2]
    totalDurationAtCompany = alltext[20][:len(alltext[20]) // 2]
    # get rest of the jobs in the same nested list
    groups = []
    count = 0
    index = 0
    for a in alltext:
        if a == '' or a == ' ':
            count += 1
        else:
            groups.append((count, index))
            count = 0
        index += 1
    numJobsInJoblist = [g for g in groups if g[0] == 21 or g[0] == 22 or g[0] == 25 or g[0] == 26]
    for i in numJobsInJoblist:
        # full time/part time case
        if 'time' in alltext[i[1] + 5][:len(alltext[i[1] + 5]) // 2].lower().split('-'):
            jobgroups.append((alltext[i[1]][:len(alltext[i[1]]) // 2], alltext[i[1] + 8][:len(alltext[i[1] + 8]) // 2]))
        else:
            jobgroups.append((alltext[i[1]][:len(alltext[i[1]]) // 2], alltext[i[1] + 4][:len(alltext[i[1] + 4]) // 2]))
    return ('type2job', company, totalDurationAtCompany, jobgroups)
# parses a type 1 job row
def parseType1Job(alltext):
    jobtitle = alltext[16][:len(alltext[16]) // 2]
    company = alltext[20][:len(alltext[20]) // 2]
    duration = alltext[23][:len(alltext[23]) // 2]
    return ('type1job', jobtitle, company, duration)
# returns linkedin profile information
def returnProfileInfo(employeeLink, companyName):
    url = employeeLink
    driver.get(url)
    time.sleep(2)
    source = BeautifulSoup(driver.page_source, "html.parser")
    profile = []
    profile.append(companyName)
    info = source.find('div', class_='mt2 relative')
    name = info.find('h1', class_='text-heading-xlarge inline t-24 v-align-middle break-words').get_text().strip()
    title = info.find('div', class_='text-body-medium break-words').get_text().lstrip().strip()
    profile.append(name)
    profile.append(title)
    time.sleep(1)
    experiences = source.find_all('li', class_='artdeco-list__item pvs-list__item--line-separated pvs-list__item--one-column')
    for x in experiences[1:]:
        alltext = x.getText().split('\n')
        print(alltext)
        startIdentifier = 0
        for e in alltext:
            if e == '' or e == ' ':
                startIdentifier+=1
            else:
                break
        # jobs, educations, certifications
        if startIdentifier == 16:
            # education
            if 'university' in alltext[16].lower().split(' ') or 'college' in alltext[16].lower().split(' ') or 'ba' in alltext[16].lower().split(' ') or 'bs' in alltext[16].lower().split(' '):
                profile.append(('education', alltext[16][:len(alltext[16])//2], alltext[20][:len(alltext[20])//2]))
            # certifications
            elif 'issued' in alltext[23].lower().split(' '):
                profile.append(('certification', alltext[16][:len(alltext[16])//2], alltext[20][:len(alltext[20])//2]))
        elif startIdentifier == 12:
            # Skills
            if (alltext[16] == '' or alltext[16] == ' ') and len(alltext) > 24:
                profile.append(('skill', alltext[12][:len(alltext[12])//2]))
    # experiences
    url = driver.current_url + '/details/experience/'
    driver.get(url)
    time.sleep(2)
    source = BeautifulSoup(driver.page_source, "html.parser")
    time.sleep(1)
    exp = source.find_all('li')
    for e in exp[13:]:
        row = e.getText().split('\n')
        if row[:16] == ['', '', '', '', '', '', ' ', '', '', '', '', '', '', '', '', '']:
            if 'yrs' in row[20].split(' '):
                profile.append(parseType2Jobs(row))
            else:
                profile.append(parseType1Job(row))
    return profile
if __name__ == "__main__":
    companies = ['royal-air-maroc','orange','inwi','maroc-telecom','ocpgroup']
    """['Deloitte','boston-consulting-group','CGI','IBM','Microsoft','Apple','Capgemini',"""
    login()
    employees = {}
    for company in companies:
        searchable = getProfileURLs(company)
        for employee in searchable[0]:
            employees[employee] = returnProfileInfo(employee, company)
   
    
   
    with open("C:\\Users\\YASSINE\\Desktop\\Mon portfolio\\Project\\Projet Python\\employees.json", "w") as output_file:
        json.dump(employees,output_file)
        print("file created")
