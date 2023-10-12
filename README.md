# Image Warping Code 


### There are two main functions (python) for warping an image to the shape of curved screen. 

### 0. Prerequisite
- As only a part of display pixels can be projected onto a screen, it is crucial to know which are the usable pixels.
- For this, we need to get 3 or more points (x, y coordinates) along the top (head) and bottom (toe) edge of the screen, in the image display space. This is important to use the same display settings (e.g., screen resolution) as the ones used for actual stimuli presentation. 
- Once those points are collected, they need to be saved in a csv file in the following format:
    - one row for each point
    - two columns for x and y coordinates
    - top points first, then bottom points
    - a blank line separates top and bottom points
    - points need to be sequential from left to right
    - end points define the edge of the warped image
    - see 'test_pointFile.csv' for an example


### 1. Computing the shape of screen
- Function: **CalcWarpRemap**
- Required Inputs:
    - **Point File:** a csv file containing points taken from the top (head) and bottom (toe) edge of screen
    - **Remap File:** name your csv file to save the remapping results
    - **Projector X, Y:** dimensions of the projection device (the same settings used to establish the input points)
    - **Image X, Y:** dimensions of the image(s) to be warped (e.g., 1024, 768)
    - **Y Expansion:** interpolation factor used in determining equal segment lengths for ellipse arcs (i.e., expected size of head_pixel/toe_pixel due to angled screen)
    - **Up Sample:** e.g., upsample * imageX, 50 * 1024 = 51200 points in the head and toe ellipses
- Note: this generates a few useful plots in a pop-up window; you can close it to proceed or just comment this part out in the code.


### 2. Map input image to the screen shape
- Function: **remapImageFile**, **warpFolderImages** (for batch job)
- Required Inputs:
    - **Input Image File:** a regular stimulus image you want to warp
    - **Remap Array:** from reading in the remap file
    - **Projector X, Y:** dimensions of the projection device (the same settings used to establish the input points)
    - **Output Image File:** name your output file to save the warped image





