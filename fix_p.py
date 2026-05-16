import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'''def percentile\(values, p\):
        if not values:
            return 0\.0
        arr = sorted\(values\)
        idx = \(len\(arr\) - 1\) \* p
        lo = math\.floor\(idx\)
        hi = math\.ceil\(idx\)
        if lo == hi:
            return float\(arr\[int\(idx\)\]\)
        return float\(arr\[lo\] \* \(hi - idx\) \+ arr\[hi\] \* \(idx - lo\)\)'''

new_code = '''def percentile(values, p):
        if not values: return 0.0
        import statistics
        return float(statistics.quantiles(values, n=100, method='inclusive')[int(p * 100) - 1]) if 0 < p < 1 else float(max(values) if p == 1 else min(values))'''

text, count = re.subn(pattern, new_code, text)
print(f"Replaced {count} instances.")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
