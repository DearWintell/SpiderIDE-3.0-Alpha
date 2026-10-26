import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FoldRegion:
 
    start_line: int
    end_line: int
    fold_type: str  
    is_collapsed: bool = False
    label: str = ""


class CodeFoldingManager:

    
    def __init__(self):
        self.fold_regions: List[FoldRegion] = []
        self.collapsed_lines: set = set() 
    
    def analyze_code(self, text: str) -> List[FoldRegion]:
        self.fold_regions = []
        lines = text.split('\n')
        
        patterns = {
            'function': r'^\s*func\s+\w+',
            'if': r'^\s*if\s+',
            'elif': r'^\s*elif\s+',
            'else': r'^\s*else\s*:',
            'while': r'^\s*while\s+',
            'for': r'^\s*for\s+',
            'loop': r'^\s*loop\s*:',
            'Spider': r'^Spider\s*\(',
        }
        
        opening_lines = []
        for i, line in enumerate(lines):
            for fold_type, pattern in patterns.items():
                if re.match(pattern, line):
                    opening_lines.append((i, fold_type, line.strip()))
                    break
        
        for start_idx, fold_type, label in opening_lines:
            end_idx = self._find_block_end(lines, start_idx)
            
            if end_idx > start_idx:  
                region = FoldRegion(
                    start_line=start_idx,
                    end_line=end_idx,
                    fold_type=fold_type,
                    is_collapsed=False,
                    label=label[:50]  
                )
                self.fold_regions.append(region)
        
        return self.fold_regions
    
    def _find_block_end(self, lines: List[str], start_idx: int) -> int:
        if start_idx >= len(lines):
            return start_idx
        

        start_line = lines[start_idx]
        start_indent = len(start_line) - len(start_line.lstrip())
        

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            

            if not line.strip():
                continue
            

            current_indent = len(line) - len(line.lstrip())
            

            if current_indent <= start_indent:
                return i - 1
        

        return len(lines) - 1
    
    def toggle_fold(self, line_number: int) -> Optional[FoldRegion]:

        for region in self.fold_regions:
            if region.start_line == line_number:
                region.is_collapsed = not region.is_collapsed
                
                if region.is_collapsed:

                    for i in range(region.start_line + 1, region.end_line + 1):
                        self.collapsed_lines.add(i)
                else:

                    for i in range(region.start_line + 1, region.end_line + 1):
                        self.collapsed_lines.discard(i)
                
                return region
        
        return None
    
    def is_line_visible(self, line_number: int) -> bool:

        return line_number not in self.collapsed_lines
    
    def get_visible_lines(self, total_lines: int) -> List[int]:

        return [i for i in range(total_lines) if self.is_line_visible(i)]
    
    def get_fold_at_line(self, line_number: int) -> Optional[FoldRegion]:

        for region in self.fold_regions:
            if region.start_line == line_number:
                return region
        return None
    
    def has_fold(self, line_number: int) -> bool:

        return any(r.start_line == line_number for r in self.fold_regions)
    
    def clear(self):

        self.fold_regions.clear()
        self.collapsed_lines.clear()
    
    def get_collapsed_count(self) -> int:

        return len(self.collapsed_lines) 