import os
import dill

from crucio.consts import projectPath


class ObjectManager:
    def __init__(self, objType):
        self.objType = objType
        self.data_dir = os.path.join(f"{projectPath}/Object", objType)
        os.makedirs(self.data_dir, exist_ok=True)

    def load(self, name):
        file_path = os.path.join(self.data_dir, name + '.pkl')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                return dill.load(file)
        else:
            raise FileNotFoundError(f"File {file_path} does not exist.")

    def loadAll(self):
        objects = {}
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.pkl'):
                name = filename[:-4]
                objects[name] = self.load(name)
        return objects

    def save(self, obj, name):
        file_path = os.path.join(self.data_dir, name + '.pkl')
        with open(file_path, 'wb') as file:
            dill.dump(obj, file)

    def remove(self,name):
        file_path = os.path.join(self.data_dir, name + '.pkl')
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    manager = ObjectManager("exampleType")

    example_obj = {"key": "value"}
    manager.save(example_obj, "example1")

    loaded_obj = manager.load("example1")
    print("Loaded:", loaded_obj)

    all_objects = manager.loadAll()
    print("All loaded objects:", all_objects)