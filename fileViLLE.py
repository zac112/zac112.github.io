files = {}

def allFilesClosed():
    for name, file in files.items():
        if file.isOpen():
            raise IOError(f"File: {name} is not closed!")

def createFile(fileName : str, content : list, mode : str="r"):
    file = VilleFile(content, mode)
    files[fileName] = file
    file.setMode(mode)
    return file

def open(fname: str, mode="r"):
    global files

    if mode == "w":
        return createFile(fname, [], mode)

    if fname in files:
        return files[fname]
    else:
        raise IOError(f"File with name {fname} not found!")

class VilleFile:
    def __init__(self, content: list, mode : str):
        if mode not in ("r","w","a","rb","r+","rw"):
            raise IOError(f"File mode {mode} not supported")

        self.__mode = mode
        self.__open = False
        self.__content = content
        if mode == "w":
            self.__content = []
        self.__pointer = 0

    def __opened_in_readmode(self):
        if not self.__open:
            raise IOError("File is closed")
        if self.__mode not in ("r","rw","rb","r+"):
            raise IOError("File is not opened in read mode")

    def __opened_in_writemode(self):
        if self.__open:
            raise IOError(f"File is closed")
        if self.__mode in ("w", "a", "rw", "r+"):
            raise IOError(f"File is not opened in write mode")

    def __enter__(self):
        self.__open = True
        self.__pointer = 0
        return self

    def __exit__(self, type, value, traceback):
        self.__open = False

    def setMode(self, mode):
        self.__mode = mode

    def read(self) -> str:
        self.__opened_in_readmode()
        return "\n".join(self.__content)


    def readline(self) -> str:
        self.__opened_in_readmode()
        if self.__pointer < len(self.__content):
            self.__pointer += 1
            return self.__content[self.__pointer - 1] 
        else: return []

    def readlines(self) -> list:
        self.__opened_in_readmode()
        return  self.__content

    def __iter__(self):
        return self

    def __next__(self):
        self.__opened_in_readmode()
        if self.__pointer < len(self.__content):
            self.__pointer += 1
            return self.__content[self.__pointer - 1]
        else:
            raise StopIteration

    def write(self,line: str):
        self.__opened_in_writemode()
        self.__content.append(line)

    def close(self):
        if self.__open:
            self.__open = False
        else:
            raise IOError("File already closed")

    def open(self):
        self.__open = True

    def isOpen(self):
        return self.__open

