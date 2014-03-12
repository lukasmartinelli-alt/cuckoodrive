@given('I have a folder with files')
def step_impl(context):
    context.folder="cuckooroot"
    context.files=[(row['name'], row['size']) for row in context.table.rows]
    print(context.files)
    assert True

@when('I execute "cuckoodrive init"')
def step_impl(context):
    assert False

@then('the folder is indexed')
def step_impl(context):
    assert False

@then('a json index file is created')
def step_impl(context):
    assert False

@then('the index file contains all the files in the folder')
def step_impl(context):
    assert False

@when('I add a provider with following settings')
def step_impl(context):
    assert False

@then('the storage provider "dropbox" is added to the index file')
def step_impl(context):
    assert False

@then('I can see the used and free space of the storage provider')
def step_impl(context):
    assert False

@then('I can see all the files of cuckoodrive on it')
def step_impl(context):
    assert False

@then('the storage provider "googledrive" is added to the index file')
def step_impl(context):
    assert False

@when('I synchronize initially')
def step_impl(context):
    assert False

@then('the files in the folder are synchronized with all the cloud storage providers')
def step_impl(context):
    assert False

@given('I have provider "googledrive" with files')
def step_impl(context):
    assert False

@given('I have provider "dropbox" with files')
def step_impl(context):
    assert False

@when('I synchronize an empty folder with the files')
def step_impl(context):
    assert False

@then('the missing files in the folder are pulled from the cloud storage providers and added again so that I have files')
def step_impl(context):
    assert False
