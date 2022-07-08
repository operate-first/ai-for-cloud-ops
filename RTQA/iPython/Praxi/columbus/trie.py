class TrieEntry:
    def __init__(self):
        self.count = 1
        self.child_list = []

class Trie:
    def __init__(self, frequency_limit=2):
        self.map = {}
        self.frequency_limit = frequency_limit

    def insert(self, token):
        if not token:
            return
        token = token.replace(':', '').replace('|', '')
        parent = None
        while len(token) >= 3:
            if token in self.map:
                self.map[token].count += 1
            else:
                self.map[token] = TrieEntry()
            if parent and parent not in self.map[token].child_list:
                self.map[token].child_list.append(parent)
            parent = token
            token = token[:-1]

    def get_all_tags(self):
        results = {}
        for token, entry in self.map.items():
            if len(entry.child_list) >= self.frequency_limit:
                results[token] = entry.count
        return results
