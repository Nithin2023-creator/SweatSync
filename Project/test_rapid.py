# listbodyparts

# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/bodyPartList"

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers)

# print(response.json())


# list excercise

# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises"

# querystring = {"sortMethod":"bodyPart","offset":"0","limit":"10","sortOrder":"ascending"}

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())



# list exercise by target

# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/target/abductors"

# querystring = {"sortOrder":"ascending","limit":"10","offset":"0","sortMethod":"bodyPart"}

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())


# search excercise by name

# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/name/glute"

# querystring = {"limit":"10","sortOrder":"ascending","sortMethod":"bodyPart","offset":"0"}

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())


# list excercise by equipment

# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/equipment/assisted"

# querystring = {"limit":"10","sortMethod":"bodyPart","sortOrder":"ascending","offset":"0"}

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())



# list excercise by id


# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/exercise/0001"

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers)

# print(response.json())


# list target

# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/targetList"

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers)

# print(response.json())



# list excercise by body part

# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/bodyPart/back"

# querystring = {"sortMethod":"bodyPart","sortOrder":"ascending","limit":"10","offset":"0"}

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())


# list equipment


# import requests

# url = "https://exercisedb.p.rapidapi.com/exercises/equipmentList"

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers)

# print(response.json())


# getexcercise image

# import requests

# url = "https://exercisedb.p.rapidapi.com/image"

# querystring = {"exerciseId":"0001","resolution":"180"}

# headers = {
# 	"x-rapidapi-key": "8e7dde9906msh5f90385f7f38167p101885jsne96c4674bbbc",
# 	"x-rapidapi-host": "exercisedb.p.rapidapi.com",
# 	"Content-Type": "application/json"
# }

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())
