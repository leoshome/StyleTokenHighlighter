import sublime
import sublime_plugin

# Color definitions using standard scopes (compatible with ST3 and ST4)
COLOR_SCOPES = [
    "string",           # Style 1
    "comment",          # Style 2
    "keyword",          # Style 3
    "constant",         # Style 4
    "support.function", # Style 5
    "variable",         # Style 6
    "entity.name.class",# Style 7
    "invalid",          # Style 8
    "storage.type"      # Style 9
]

class StyleTokenHighlightCommand(sublime_plugin.TextCommand):
    def description(self, color_index=0):
        return "Using Style {}".format(color_index + 1)

    def run(self, edit, color_index=0):
        view = self.view
        sel = view.sel()
        
        scope = COLOR_SCOPES[color_index % len(COLOR_SCOPES)]
        key = "style_token_{}".format(color_index)
        
        new_regions = view.get_regions(key)
        
        for region in sel:
            word_region = view.word(region) if region.empty() else region
            text = view.substr(word_region)
            if not text.strip(): continue
            
            matches = view.find_all(text, sublime.LITERAL)
            for m in matches:
                if m not in new_regions:
                    new_regions.append(m)
        
        view.add_regions(key, new_regions, scope, "", sublime.DRAW_NO_OUTLINE | sublime.PERSISTENT)

class StyleTokenClearSpecificHighlightCommand(sublime_plugin.TextCommand):
    def description(self, color_index=0):
        return "Clear Style {}".format(color_index + 1)

    def run(self, edit, color_index=0):
        key = "style_token_{}".format(color_index)
        self.view.erase_regions(key)

class StyleTokenClearAllHighlightCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for i in range(len(COLOR_SCOPES)):
            self.view.erase_regions("style_token_{}".format(i))

class StyleTokenToggleSpecificHighlightCommand(sublime_plugin.TextCommand):
    def description(self, color_index=0):
        return "Toggle Style {}".format(color_index + 1)

    def run(self, edit, color_index=0):
        view = self.view
        sel = view.sel()
        
        scope = COLOR_SCOPES[color_index % len(COLOR_SCOPES)]
        key = "style_token_{}".format(color_index)
        
        existing_regions = view.get_regions(key)
        
        for region in sel:
            word_region = view.word(region) if region.empty() else region
            text = view.substr(word_region)
            if not text.strip():
                continue
            
            matches = view.find_all(text, sublime.LITERAL)
            
            # Check if any match is already highlighted
            is_highlighted = any(m in existing_regions for m in matches)
            
            if is_highlighted:
                # Remove all matches from existing regions (toggle off)
                existing_regions = [r for r in existing_regions if r not in matches]
            else:
                # Add all matches to existing regions (toggle on)
                for m in matches:
                    if m not in existing_regions:
                        existing_regions.append(m)
        
        # Update regions
        if existing_regions:
            view.add_regions(key, existing_regions, scope, "", sublime.DRAW_NO_OUTLINE | sublime.PERSISTENT)
        else:
            view.erase_regions(key)

class StyleTokenToggleHighlightCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()
        
        # Find first available style
        color_index = self._get_next_available_style(view)
        
        scope = COLOR_SCOPES[color_index % len(COLOR_SCOPES)]
        key = "style_token_{}".format(color_index)
        
        existing_regions = view.get_regions(key)
        
        for region in sel:
            word_region = view.word(region) if region.empty() else region
            text = view.substr(word_region)
            if not text.strip():
                continue
            
            matches = view.find_all(text, sublime.LITERAL)
            
            # Check if matches are already highlighted in any style
            is_highlighted, highlighted_key = self._is_text_highlighted(view, matches)
            
            if is_highlighted:
                # Remove highlight from the original key
                highlighted_regions = view.get_regions(highlighted_key)
                new_regions = [r for r in highlighted_regions if r not in matches]
                if new_regions:
                    view.add_regions(highlighted_key, new_regions, 
                        COLOR_SCOPES[int(highlighted_key.split('_')[-1]) % len(COLOR_SCOPES)], 
                        "", sublime.DRAW_NO_OUTLINE | sublime.PERSISTENT)
                else:
                    view.erase_regions(highlighted_key)
                sublime.status_message("StyleToken: Removed highlight (Style {})".format(int(highlighted_key.split('_')[-1]) + 1))
            else:
                # Add highlight to the selected style
                for m in matches:
                    if m not in existing_regions:
                        existing_regions.append(m)
                view.add_regions(key, existing_regions, scope, "", sublime.DRAW_NO_OUTLINE | sublime.PERSISTENT)
                sublime.status_message("StyleToken: Added highlight (Style {})".format(color_index + 1))
    
    def _get_next_available_style(self, view):
        """Find the first unused style index, return 0 if all are used"""
        for i in range(len(COLOR_SCOPES)):
            key = "style_token_{}".format(i)
            regions = view.get_regions(key)
            if not regions:
                return i
        # All styles are used, cycle back to the first one
        return 0
    
    def _is_text_highlighted(self, view, matches):
        """Check if text is already highlighted in any style"""
        for i in range(len(COLOR_SCOPES)):
            key = "style_token_{}".format(i)
            regions = view.get_regions(key)
            if any(m in regions for m in matches):
                return True, key
        return False, None

class StyleTokenGoNextCommand(sublime_plugin.TextCommand):
    def run(self, edit, color_index=None):
        view = self.view
        
        # Auto-detect color index if cursor is inside a highlighted region
        if color_index is None:
            color_index = self._get_color_index_at_cursor(view)
            if color_index is None:
                sublime.status_message("StyleToken: No highlight found at cursor position")
                return
        
        key = "style_token_{}".format(color_index)
        regions = view.get_regions(key)
        
        if not regions:
            sublime.status_message("StyleToken: No regions for style {}".format(color_index + 1))
            return
        
        # Get current cursor position
        cursor_pos = view.sel()[0].begin()
        
        # Find next region
        next_region = None
        for region in regions:
            if region.begin() > cursor_pos:
                next_region = region
                break
        
        # Wrap around to first if at end
        if next_region is None and regions:
            next_region = regions[0]
        
        if next_region:
            view.sel().clear()
            view.sel().add(next_region)
            view.show_at_center(next_region)
            sublime.status_message("StyleToken: Go to next highlight (Style {})".format(color_index + 1))
    
    def _get_color_index_at_cursor(self, view):
        """Detect which color highlight the cursor is inside"""
        cursor_pos = view.sel()[0].begin()
        
        for i in range(len(COLOR_SCOPES)):
            key = "style_token_{}".format(i)
            regions = view.get_regions(key)
            for region in regions:
                if region.contains(cursor_pos):
                    return i
        return None

class StyleTokenGoPrevCommand(sublime_plugin.TextCommand):
    def run(self, edit, color_index=None):
        view = self.view
        
        # Auto-detect color index if cursor is inside a highlighted region
        if color_index is None:
            color_index = self._get_color_index_at_cursor(view)
            if color_index is None:
                sublime.status_message("StyleToken: No highlight found at cursor position")
                return
        
        key = "style_token_{}".format(color_index)
        regions = view.get_regions(key)
        
        if not regions:
            sublime.status_message("StyleToken: No regions for style {}".format(color_index + 1))
            return
        
        # Get current cursor position
        cursor_pos = view.sel()[0].begin()
        
        # Find previous region
        prev_region = None
        for region in reversed(regions):
            if region.end() < cursor_pos:
                prev_region = region
                break
        
        # Wrap around to last if at beginning
        if prev_region is None and regions:
            prev_region = regions[-1]
        
        if prev_region:
            view.sel().clear()
            view.sel().add(prev_region)
            view.show_at_center(prev_region)
            sublime.status_message("StyleToken: Go to previous highlight (Style {})".format(color_index + 1))
    
    def _get_color_index_at_cursor(self, view):
        """Detect which color highlight the cursor is inside"""
        cursor_pos = view.sel()[0].begin()
        
        for i in range(len(COLOR_SCOPES)):
            key = "style_token_{}".format(i)
            regions = view.get_regions(key)
            for region in regions:
                if region.contains(cursor_pos):
                    return i
        return None
