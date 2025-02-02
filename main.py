import sys
import os

# Add the project directory to sys.path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

from src.interfaces.menu import MainMenu

def main():
    app = MainMenu()
    app.run()

if __name__ == "__main__":
    main()
