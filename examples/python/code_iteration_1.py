"""
SPDX-License-Identifier: Apache-2.0
Copyright : JPMorganChase

CodeQUEST 
(
    Code Quality Understanding and 
    Enhancement System Toolkit
)
"""

class Node:
    """
    A class to represent a node in a binary tree.

    Attributes:
    data : any type
        The data stored in the node.
    left : Node
        The left child node.
    right : Node
        The right child node.
    """
    def __init__(self, data):
        """
        Constructs all the necessary attributes for the node object.

        Parameters:
        data : any type
            The data stored in the node.
        """
        self.data = data
        self.left = None
        self.right = None

def max_height(node):
    """
    Calculate the maximum height of a binary tree.

    Parameters:
    node : Node
        The root node of the binary tree.

    Returns:
    int
        The maximum height of the binary tree.
    """
    if not isinstance(node, Node) and node is not None:
        raise ValueError("Input must be a Node object or None")

    if node is None:
        return 0

    # Use an iterative approach with a stack to avoid deep recursion
    stack = [(node, 1)]
    max_height = 0

    while stack:
        current_node, current_height = stack.pop()
        if current_node:
            max_height = max(max_height, current_height)
            stack.append((current_node.left, current_height + 1))
            stack.append((current_node.right, current_height + 1))

    return max_height
