# Overview
This files contains the learnings I gained as a part of the building and learning process

> Credits for the initial push: https://www.youtube.com/watch?v=JzK-QksLYcg&t=4s

### Why to put 0.0.0.0 in the server address but to put localhost in the server uri?
The first one shows that the server accepts requests from any source and the second one is the address of the local server running on the PC at 127.0.0.1 or localhost

### Why resource accessed as file:// not accessible and gives None type session object?
The issue is not with the coding but the way path is written. The path to the file 
resource should be file:///logs.txt and not file://logs.txt. Mind it!