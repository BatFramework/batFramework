# batFramework

batFramework is a Python game framework built using Pygame, designed to simplify game development by providing entities, scenes, a scene manager, and various utilities.

## Purpose and Overview
The primary objective of batFramework is to streamline game development by utilizing entities and scenes that hold entities. It employs a manager, which inherits from the scene manager, to handle scenes, propagate events, and manage updates and rendering.

## Installation and Setup
To install batFramework, you can use pip:
```pip install batFramework```


The only dependency required is pygame-ce.

## Usage Instructions
To create a basic app using batFramework, here's an example:

```python
import batFramework as bf

# Initialize the framework
bf.init((1280, 720), window_title="My Amazing Program")

# Create a manager and a scene
bf.Manager(bf.Scene("main")).run()
```
In practice, users can inherit bf.Scene to create their own scenes, adding specific behaviors, entities, etc.

## Features and Functionalities

- Scene management for organizing game components
- Cutscene support to facilitate storytelling sequences
- Audio management for music and sound effects with volume control
- Entity, sprite, and animated sprite support
- Utility modules such as time management and easingAnimation

Users can leverage these functionalities to build games efficiently using batFramework.

For more detailed usage and examples, please refer to the documentation or codebase.


# License
 MIT License


