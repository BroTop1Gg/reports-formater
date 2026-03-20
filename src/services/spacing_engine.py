"""
Spacing Engine for Reports-Formater.

Middleware that injects `BreakData` nodes between content nodes
based on the configured spacing rules, ensuring DSTU 3008-2015 compliance.
"""

import logging
from typing import List, Dict, Any, Set

from src.config.schemas import AnyContentNode, BreakData

logger = logging.getLogger(__name__)


class SpacingEngine:
    """
    Middleware for automatically injecting spacing between content nodes.
    
    Implements Margin Collapsing and respects user-defined manual breaks
    or page markers to prevent redundant empty lines.
    """
    
    def __init__(self, rules: Dict[str, Dict[str, Any]]):
        """
        Initialize the SpacingEngine.
        
        Args:
            rules: Configuration dict mapping node types to spacing rules.
        """
        self.rules = rules

    def process(self, nodes: List[AnyContentNode]) -> List[AnyContentNode]:
        """
        Process a list of parsed content nodes, injecting BreakData where needed.
        
        Args:
            nodes: The original parsed content nodes.
            
        Returns:
            A new list of content nodes with BreakData injected.
        """
        if not nodes:
            return []

        result: List[AnyContentNode] = []
        auto_breaks: Set[int] = set()
        n = len(nodes)

        for i, node in enumerate(nodes):
            # 1. Identify if the current node is a manual break or page marker
            is_manual_break = False
            is_page_marker = False
            
            if node.type == "break":
                style = getattr(node, "style", "line")
                if style in ["page", "section"]:
                    is_page_marker = True
                elif style == "line" and id(node) not in auto_breaks:
                    is_manual_break = True
            elif node.type == "page_break":
                is_page_marker = True
            elif node.type == "paragraph":
                # Treat empty paragraphs as manual breaks to support legacy templates
                text_val = getattr(node, "text", "")
                if isinstance(text_val, str) and not text_val.strip():
                    is_manual_break = True

            # If we encountered a user-defined manual break or page marker, 
            # suppress/remove any trailing auto-break that we just generated.
            if is_manual_break or is_page_marker:
                if result and result[-1].type == "break" and id(result[-1]) in auto_breaks:
                    removed_break = result.pop()
                    auto_breaks.remove(id(removed_break))

            # 2. Extract spacing requirements for the current node
            rule = None
            if node.type == "heading":
                level = getattr(node, "level", None)
                if level is not None:
                    rule_key = f"heading_{level}"
                    if rule_key in self.rules and self.rules[rule_key] is not None:
                        rule = self.rules[rule_key]
            
            if rule is None:
                rule = self.rules.get(node.type, {})
                
            req_before = rule.get("before", 0)
            req_after = rule.get("after", 0)

            if rule.get("skip_if_first") and i == 0:
                req_before = 0
            if rule.get("skip_if_last") and i == n - 1:
                req_after = 0

            # 3. Apply req_before
            if req_before > 0:
                if not result:
                    auto_b = BreakData(type="break", style="line", count=req_before)
                    auto_breaks.add(id(auto_b))
                    result.append(auto_b)
                else:
                    prev_node = result[-1]
                    
                    is_prev_page_marker = prev_node.type == "page_break" or (
                        prev_node.type == "break" and getattr(prev_node, "style", "line") in ["page", "section"]
                    )
                    
                    is_prev_manual_break = False
                    is_prev_auto_break = False
                    
                    if prev_node.type == "break" and getattr(prev_node, "style", "line") == "line":
                        if id(prev_node) in auto_breaks:
                            is_prev_auto_break = True
                        else:
                            is_prev_manual_break = True
                    elif prev_node.type == "paragraph":
                        text_val = getattr(prev_node, "text", "")
                        if isinstance(text_val, str) and not text_val.strip():
                            is_prev_manual_break = True
                    
                    # Margin collapsing and overriding
                    if is_prev_page_marker or is_prev_manual_break:
                        # Required spacing is suppressed by user or page boundary
                        pass
                    elif is_prev_auto_break:
                        # Standard margin collapse: take max(previous auto break, required new break)
                        prev_node.count = max(prev_node.count, req_before)
                    else:
                        auto_b = BreakData(type="break", style="line", count=req_before)
                        auto_breaks.add(id(auto_b))
                        result.append(auto_b)

            # 4. Append the actual node
            result.append(node)

            # 5. Apply req_after
            if req_after > 0:
                auto_b = BreakData(type="break", style="line", count=req_after)
                auto_breaks.add(id(auto_b))
                result.append(auto_b)

        return result
