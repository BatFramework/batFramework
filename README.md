# batFramework

batFramework is a Python game framework built using Pygame, designed to simplify game development.

## Purpose and Overview
The primary objective of batFramework is to streamline game development. It is mainly designed to program small 2D games

## Installation and Setup
To install batFramework, you can use pip:
```pip install batFramework```

The only dependency required is pygame-ce.

## Usage Instructions
To create a basic app using batFramework, here's an example:

```python
import batFramework as bf

# Initialize the framework
bf.init(resolution=(1280, 720), window_caption="My Amazing Program")

# Create a manager and a scene
bf.Manager(bf.Scene("main")).run()
```
In practice, users can inherit bf.Scene to create their own scenes, adding specific behaviors, entities, etc.

## Features and Functionalities

For more detailed information, please refer to the [documentation](https://batframework.github.io/batDocumentation/).


# License
 MIT License


