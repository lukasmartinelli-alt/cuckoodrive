from os import urandom
from fs.memoryfs import MemoryFS

def create_random_file(fs, filename, filesize):
	with fs.open(filename, "w") as file:
		file.write(str(urandom(filesize // 1000)))

@given('I have a folder with files')
def step_impl(context):
	context.fs = MemoryFS()
	fs.makedir('cuckoodrive')
	[create_random_file(row['name'], int(row['size'])) for row in context.table.rows]
	context.local_fs = local_fs

@when('I initialize the folder')
def step_impl(context):
    assert False
