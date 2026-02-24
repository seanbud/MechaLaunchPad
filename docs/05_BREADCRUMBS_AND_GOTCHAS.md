# 05. UI/UX Gotchas and Lessons

Building a cross-platform desktop app with PySide6 (Qt) comes with strict layout and styling behaviors that must be respected to maintain a premium feel. 

If you are expanding the `MainWindow` or custom widgets like `CIJobCard`, remember these critical lessons learned:

## 1. The Global Resource Token Pattern
**Do not hardcode hex colors throughout the application!** 
All colors, font sizes, and layout constants are stored centrally in `app/core/resources.py` inside the `StyleTokens` class. 

For example, when setting text color:
`widget.setStyleSheet(f"color: {StyleTokens.TEXT_MAIN};")`

If you hardcode `#FFFFFF`, you break the ability to easily generate Light/Dark themes in the future.

## 2. Inverted Inheritance (The Black on Black Bug)
PyQt widgets aggressively inherit CSS styling from their parents. 

Early on, we styled the main application window background to be Dark Slate (`#1E1C22`), and explicitly told `QLabel` text to act as `TEXT_MAIN` (white).

However, complex widgets like `QTextEdit` or `QScrollArea` naturally inherit their container's dark background, but often default their *internal text color* to system settings (which is black on Windows!). This resulted in entirely unreadable black text on black backgrounds!

**The Fix:** You must explicitly enforce transparency or border rules when nesting complex containers, OR explicitly re-declare the contrasting colors deep in the tree. 
*Example Fix:* `self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")`

## 3. The 100% Zoom Default
When expanding the canvas preview or generating heavy data layouts, ensure the UI is explicitly programmed to reset to a defined state. 

We explicitly enforce a "100% Zoom Level Default" rule whenever new widgets are hydrated in tabs to keep the 3D Artist's perspective stable across application switching. (E.g. They shouldn't swap back to a tab and find the preview shrunk into a tiny corner because a canvas state leaked).
