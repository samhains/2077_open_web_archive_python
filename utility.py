import os

def search_query_from_str(str):
    return str.replace(" ", "+")

def make_folder(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

def delete_old(folder_name):
    for the_file in os.listdir(folder_name):
        file_path = os.path.join(folder_name, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)
