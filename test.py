from src.algorithms.utils import save_object_to_pickle_file, load_object_from_pickle_file
l = [1,2,3]

save_object_to_pickle_file(l, "test")
print(load_object_from_pickle_file("test"))