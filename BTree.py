class BTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf  # 是否是叶子结点
        self.keys = []  # 存储 (key, [values]) 键值对
        self.children = []  # 存储子节点

class BTree:
    def __init__(self, t):
        self.root = BTreeNode(True)  # 创建根节点
        self.t = t  # 最小度数（决定树的结构）

    def search(self, key, node=None):
        """在 B-Tree 中搜索 key 对应的 values（list）"""
        if node is None:
            node = self.root

        i = 0
        while i < len(node.keys) and node.keys[i][0] < key:  
            i += 1

        if i < len(node.keys) and node.keys[i][0] == key:  
            return node.keys[i][1]  # 返回 values 列表

        if node.leaf:  
            return None

        return self.search(key, node.children[i])

    def insert(self, key, value):
        """插入 (key, value) 到 B-Tree"""
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:  
            new_root = BTreeNode(False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root  
        self._insert_non_full(self.root, key, value)

    def _insert_non_full(self, node, key, value):
        """向非满节点插入 (key, value)"""
        i = len(node.keys) - 1
        if node.leaf:
            while i >= 0 and node.keys[i][0] > key:  
                i -= 1
            if i >= 0 and node.keys[i][0] == key:  
                node.keys[i][1].append(value)  # 追加到已有 key
            else:
                node.keys.insert(i + 1, (key, [value]))  
        else:
            while i >= 0 and node.keys[i][0] > key:
                i -= 1
            i += 1
            if len(node.children[i].keys) == (2 * self.t) - 1:  
                self._split_child(node, i)
                if key > node.keys[i][0]:  
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent, i):
        """分裂一个满的子节点"""
        t = self.t
        full_child = parent.children[i]
        new_child = BTreeNode(full_child.leaf)

        parent.keys.insert(i, full_child.keys[t - 1])  
        parent.children.insert(i + 1, new_child)

        new_child.keys = full_child.keys[t:]  
        full_child.keys = full_child.keys[:t - 1]  

        if not full_child.leaf:  
            new_child.children = full_child.children[t:]
            full_child.children = full_child.children[:t]

    def traverse(self, node=None):
        """遍历 B-Tree，按 key 递增顺序打印"""
        if node is None:
            node = self.root

        for i in range(len(node.keys)):
            if not node.leaf:
                self.traverse(node.children[i])
            print(f"{node.keys[i][0]}: {node.keys[i][1]}", end="  ")

        if not node.leaf:
            self.traverse(node.children[-1])




