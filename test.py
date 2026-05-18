from functools import wraps

class JB0:
    def __init__(self, value = 10):
        self.value = value

        @self.w1
        def get_value(p = False):
            if p:
                print(self.value)
            return self.value
        
        self.jbm = get_value

    def w1(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print("wrapping1")
            return func(*args, **kwargs)
        return wrapper
    
    def w2(self, func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            print("wrapping2")
            return func(self, *args, **kwargs)
        return wrapper
    
jb0 = JB0()

jb0.jbm(p = True)