import os
import csv
import glob
import math

# --- Core Mock Classes ---

class Column:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, item):
        return Column(f"{self.name}.{item}")
    
    def __call__(self, *args, **kwargs):
        return MethodCall(self, args, kwargs)

    def __eq__(self, other):
        return Expression("eq", self, other)

class MethodCall:
    def __init__(self, col, args, kwargs):
        self.col = col
        self.args = args
        self.kwargs = kwargs

class Expression:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class This:
    def __getattr__(self, item):
        return Column(item)

this = This()

def apply(func, *args):
    return Apply(func, args)

class Apply:
    def __init__(self, func, args):
        self.func = func
        self.args = args

def evaluate(expr, row, extra_context=None):
    if isinstance(expr, Column):
        # Handle nested access if needed, simple for now
        val = row.get(expr.name)
        if val is None and "." in expr.name:
            parts = expr.name.split(".")
            val = row
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p)
                else: 
                    val = getattr(val, p, None)
        return val
    elif isinstance(expr, Apply):
        resolved_args = [evaluate(a, row, extra_context) for a in expr.args]
        return expr.func(*resolved_args)
    elif isinstance(expr, MethodCall):
        func = evaluate(expr.col, row, extra_context)
        r_args = [evaluate(a, row, extra_context) for a in expr.args]
        # minimal kwargs support if needed
        return func(*r_args)
    elif isinstance(expr, Expression):
        left = evaluate(expr.left, row, extra_context)
        right = evaluate(expr.right, row, extra_context)
        if expr.op == "eq":
            return left == right
    elif isinstance(expr, tuple): # For reducers.tuple
         return tuple(evaluate(x, row, extra_context) for x in expr)
    elif isinstance(expr, list):
         return [evaluate(x, row, extra_context) for x in expr]
    return expr

class Table:
    def __init__(self, data):
        self.data = data # List of dicts

    def __getattr__(self, item):
        return Column(item)

    def select(self, **kwargs):
        new_data = []
        for row in self.data:
            new_row = {}
            for key, expr in kwargs.items():
                new_row[key] = evaluate(expr, row)
            new_data.append(new_row)
        return Table(new_data)

    def flatten(self, col):
        new_data = []
        for row in self.data:
            items = evaluate(col, row)
            if isinstance(items, list):
                for item in items:
                    # new_row = row.copy() # In pathway flatten usually keeps other cols? 
                    # The usage in pathway_flow implies we select specific fields. 
                    # Actually flatten in Pathway explodes the row. 
                    # The usage: novels.select(... chunk=...).flatten(pw.this.chunk)
                    # This usually makes 'chunk' the item itself or similar.
                    # Let's assume it keeps all columns but replaces the flattened column with the item
                    new_row = row.copy()
                    new_row[col.name] = item
                    new_data.append(new_row)
        return Table(new_data)

    def filter(self, expr):
        new_data = []
        for row in self.data:
            if evaluate(expr, row):
                new_data.append(row)
        return Table(new_data)

    def join(self, other_table, condition, right_name=None):
        # Minimal join support for the KNN case
        # usage: matches = claim_vectors.join(novel_vectors, pw.knn(...), right_name="novel")
        # In this mock, we'll let the "condition" (knn) generate the matches
        
        if isinstance(condition, KnnExpression):
             return condition.execute(self, other_table, right_name)
        
        return Table([])

    def groupby(self, *keys):
        return GroupedTable(self.data, keys)
    
class GroupedTable:
    def __init__(self, data, keys):
        self.data = data
        self.keys = keys # Column objects
    
    def reduce(self, **kwargs):
        # 1. Group
        groups = {}
        if not self.keys:
            # Global reduction if no keys
            group_key = ()
            groups[group_key] = self.data
        else:
             for row in self.data:
                # key values
                group_key_vals = []
                for k in self.keys:
                    group_key_vals.append(evaluate(k, row))
                group_key = tuple(group_key_vals)
                
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(row)
            
        # 2. Reduce
        new_data = []
        for group_key, rows in groups.items():
            new_row = {}
            # Add grouping keys back
            for i, k in enumerate(self.keys):
                # Simple name extraction, assuming direct columns
                new_row[k.name] = group_key[i]
                
            for res_name, reducer in kwargs.items():
                # reducer is standard tuple reducer in the flow
                # usage: relevant_chunks=pw.reducers.tuple(pw.this.novel_chunk)
                new_row[res_name] = reducer.execute(rows)
            new_data.append(new_row)
            
        return Table(new_data)

class Reducers:
    def tuple(self, col):
        return TupleReducer(col)

reducers = Reducers()

class TupleReducer:
    def __init__(self, col):
        self.col = col
    def execute(self, rows):
        res = []
        for r in rows:
            res.append(evaluate(self.col, r))
        return tuple(res)

# --- IO ---

class IO:
    class FS:
        @staticmethod
        def read(path, format="binary", mode="static", with_metadata=True):
            # Read all files in path
            # returns Table with data, path, etc.
            wildcard = os.path.join(path, "*")
            files = glob.glob(wildcard)
            rows = []
            for f in files:
                with open(f, "rb") as open_f:
                    content = open_f.read()
                    rows.append({
                        "path": f,
                        "data": content,
                        "created_at": 0,
                        "modified_at": 0
                    })
            return Table(rows)
    
    class CSV:
        @staticmethod
        def write(table, filename):
             if not table.data:
                 return
             keys = table.data[0].keys()
             os.makedirs(os.path.dirname(filename), exist_ok=True)
             with open(filename, "w", newline="") as f:
                 writer = csv.DictWriter(f, fieldnames=keys)
                 writer.writeheader()
                 writer.writerows(table.data)
             print(f"Mock Pathway: Wrote {len(table.data)} rows to {filename}")

    fs = FS
    csv = CSV

io = IO

# --- ML / KNN ---

def knn(left_vec, right_vec, k=5):
    return KnnExpression(left_vec, right_vec, k)

class KnnExpression:
    def __init__(self, left_vec, right_vec, k):
        self.left_vec = left_vec
        self.right_vec = right_vec
        self.k = k
    
    def execute(self, left_table, right_table, right_name):
        print("Mock Pathway: Starting KNN Join...")
        joined_rows = []
        
        l_cnt = len(left_table.data)
        r_cnt = len(right_table.data)
        print(f"Mock Pathway: Left rows: {l_cnt}, Right rows: {r_cnt}")
        
        # Optimization: Pre-compute right norms
        r_cache = []
        for r_row in right_table.data:
            r_v = evaluate(self.right_vec, r_row)
            norm = math.sqrt(sum(a*a for a in r_v))
            r_cache.append((r_v, norm, r_row))

        for i, l_row in enumerate(left_table.data):
            if i % 10 == 0:
                print(f"Mock Pathway: Processing left row {i}/{l_cnt}...", end="\r")
            
            l_v = evaluate(self.left_vec, l_row)
            l_norm = math.sqrt(sum(a*a for a in l_v))
            
            scores = []
            for r_v, r_norm, r_row in r_cache:
                # Fast path for identical mock vectors
                # If both are [0.1]*1536, sum is 1536*(0.1*0.1) = 15.36
                if l_v == r_v:
                     score = 1.0
                else:
                    dot = sum(a*b for a,b in zip(l_v, r_v))
                    score = dot / ((l_norm * r_norm) + 1e-9)
                scores.append((score, r_row))
            
            scores.sort(key=lambda x: x[0], reverse=True)
            top_k = scores[:self.k]
            
            for score, r_row in top_k:
                new_row = l_row.copy()
                for k, v in r_row.items():
                    key_name = f"{right_name}_{k}" if right_name else k
                    new_row[key_name] = v
                joined_rows.append(new_row)
        
        print(f"\nMock Pathway: KNN Join complete. Total joined rows: {len(joined_rows)}")
        return Table(joined_rows)

    def cosine_similarity(self, v1, v2):
        # Unused now
        pass

# --- UDF ---

def udf(func):
    def wrapper(*args, **kwargs):
        return Apply(func, args)
    return wrapper

# --- Engine ---

def run():
    print("Mock Pathway: Pipeline run complete (simulated).")
