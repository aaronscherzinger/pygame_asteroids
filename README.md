# A simple Asteroids-like game written in Python

## Description

This is old code I wrote several years back just to look into Python and check out pygame while implementing a geometric collision detection mechanism for 2D polygons. Please keep in mind that this implementation is not necessarily very efficient (also, writing games in Python is probably not the best idea, anyway). I have recently tested this code on Linux Mint 19 with an Intel Core i7-4790K where it runs fine, but do not know about any other system configurations.

In order to run this, you will need Python 3 and have [pygame](https://www.pygame.org) installed. 

## Notes about the implementation

The collision detection is only evaluated at discrete time points, i.e., in every frame. If frame rates get too low on your system, this might be problematic, since objects might move through each other in between two frames. In order to fix this, the collision detection would have to be more complex, which was out of scope for this little project at the time I wrote it. If you are interested in this, there is a GDC talk by Erin Catto which contains some ideas to implement a more complex collision detection system: https://youtu.be/7_nKOET6zwI

Since in Asteroids, the screen wraps at the edges, I chose to implement to most simple solution: just check where an object needs to wrap around and render duplicates of it if necessary. Also for the collision detection, the object is simply temporarily translated to the corresponding location. There is a lot of optimization potential here in order to speed up collision computations, e.g., by using a grid data structure to omit a lot of the collision checks (however, there is already an optimzation which checks bounding boxes first).

I have not changed anything in the code before uploading it, so it is just what I wrote several years back for myself (including several TODO-statements that I just left in there).

## Music

The music was a spontaneous improvisation recorded with a friend of mine in my appartment and had nothing to do with this game, but since I wanted to test the pygame music player, I used what was available at the moment. So I just include it here. I would be nice to contact me if you want to use it for anything. 

## Controls

Start the game with '''python3 asteroids.py'''. The first startup might take a while if pygame needs to load the font.

You control your spaceship with the arrow keys (up, right, and left) and shoot with the space bar. The escape key will pause the game and the f key will show the frame rate. Exit the application by closing the window.
