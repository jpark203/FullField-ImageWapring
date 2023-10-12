# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 16:48:57 2023

@author: Ed"""
import sys
import pandas as pd 
import numpy as  np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import cv2
import os




#Main function is here
def CalcWarpRemap(pointFile, remapfile, projx, projy, imagex, imagey, yexpansion, upsample):
    #typical values projx=3840(2560), projy=2160(1080), imagex=1024, imagey768, yexpansion=0.86, upsample=50
    #projx/y are the image dimensions of the projection device (same settings used to establish screen points)
    #imagex/y are dimensions of the image(s) to be warped
    #y expansion is expected size of headpixel/toepixel due to angled screen ~sec(theta_head)**2/sec(theta_toe)**2 
    #interpolation factor used in determining equal segment lengths for ellipse arcs,
    #e.g. upsample*imagex, 50*1024=51200 points in the head and toe ellipses
    #upsample=50 
      
    
    #read file containing points taken from top(head) and bottom(toe) edge of screen
    headpoints, toepoints=readPointFile(pointFile)
   
   
    #create a LUT for mapping Y projections to account for pixel stretching due to changing incidence angle
    ystretch= np.cumsum(np.linspace(yexpansion, 1, num=imagey))
    ystretch=(ystretch/np.amax(ystretch))*(imagey-1)
    
    #divide the top and bottom ellipse fits into equal length segments 
    #these pairs of points (one from teh top, the other bottom) define the rays or spokes 
    #that deliniate lines of constant x in the warped space
    headCrossings,headx, heady=segmentEllipse(headpoints, 50, projx, imagex)
    toeCrossings, toex, toey=segmentEllipse(toepoints, 50, projx, imagex)
    
    #calculate the length of each ray(spoke) 
    raydist=(headCrossings-toeCrossings)**2
    raydist=(np.sum(raydist,axis=1))**0.5
    
    #each ray can be represendted as a line of the form ax+by+c=0
    #where, a=y2-y1, b=x1-x2 (yes reversed),c=y1x2-y2x1
    #the distance of any arbitry point (x,y) to such a line is giveb by dist=|ax+by+c|/sqrt(a^2+b^2)
    a=toeCrossings[:,1]-headCrossings[:,1]
    b=headCrossings[:,0]-toeCrossings[:,0]
    c=headCrossings[:,1]*toeCrossings[:,0]-toeCrossings[:,1]*headCrossings[:,0]
    d=(a**2+b**2)**0.5
    
    

    xstart=int(headpoints[0,0]) #assumes head ellipse is largest x span, true for us
    xend=int(headpoints[-1,0])
    ystart=int(np.amin(heady))
    yend=int(np.amax(toey))
    size=(xend-xstart+1)*(yend-ystart+1)
    #preallocate a large array to hold all possible remapped values within ROI
    linepoints=np.zeros([size,4],dtype='int16')
   
    #for every pixel in the ROI find the closest ray(spoke)
    #determine if the point is between the head and toe ellipses
    #and between the first and last ray
    #if so add it to the preallocated array
    print (xstart, xend, ystart, yend)
    print("\n\n\n")
    
    k=0
    for i in range(xstart, xend):
        if i%20==0:
            sys.stdout.write("  \r Iteration %d out of %d" % (i,xend))
        for j in range(ystart, yend ):
            #calc distance from projector point to all rays/spokes, find the closest
            linedist=abs(a*i+b*j+c)/d
            raynum=np.argmin(linedist)
            #measure distance from point to endpoints of the closest ray
            yheaddist=((headCrossings[raynum,0]-i)**2+(headCrossings[raynum,1]-j)**2)**0.5
            ytoedist=((toeCrossings[raynum,0]-i)**2+(toeCrossings[raynum,1]-j)**2)**0.5
            #confirm that the point is between the left and right bounding rays and that it 
            #lies between the ray endpoints, if so store the projector pixel values as well
            #as the corresponding image pixel value
            if (0<raynum<imagex) and (yheaddist<=raydist[raynum]) and (ytoedist<=raydist[raynum]):
                ypix=ystretch[int(np.floor(yheaddist/raydist[raynum]*imagey))]
                linepoints[k,:]=i,j,raynum,ypix
                k+=1
    
    sys.stdout.write(" \r Done                                        ")            
    sys.stdout.write(" \r Saving File                                        ")            
    remap=np.resize(linepoints,(k,4))
    #save the remap to a file and return it     
    np.savetxt(remapfile, remap, delimiter=",") 
    
    return remap
      

"""**********************************************************************************************"""
def readPointFile(pointFile):
    #read file containing points taken from top(head) and bottom(toe) edge of screen
    #points are sequential from left-right. Endpoints define the edge of the warped image
    #file is text CSV of the form X,Y with a newline for each head point. 
    #a blank line separates points from the top and bottom of the screen 
    #data is stored in headpoints, toepoints
    myFile = pd.read_csv(pointFile, sep=',', header=None, skip_blank_lines=False)
    points=myFile.to_numpy(float)
    breakdetected=False
    headpoints=np.empty([0,2])
    toepoints=np.empty([0,2])
    
    # Loop through the read CSV rows split head/toe points at line break
    for x in points:
          
        myarray=np.asarray(x)
        myarray=np.reshape(myarray,[1,2])
        # if a blank line has been encountered, add data to toepoints
        if breakdetected:
            toepoints=np.concatenate( (toepoints, myarray), axis=0)
        else:
            # If an empty line has not been detected, check or append data to headpoints
            if np.isnan(x[0]):
                breakdetected=True
            else:
               headpoints=np.concatenate((headpoints, myarray), axis=0)

    return headpoints, toepoints

"""***************************************************************************************************"""

#This function fits measured screen points to ellipse and segments it into equal arcs

def segmentEllipse(measuredPoints, upsample, projx, imagex):
    initial_guess = (projx/2, 30000, projx/2, projx/2)
    x_data=measuredPoints[:,0]
    y_data=measuredPoints[:,1]
    ones=np.empty (len(x_data), dtype=float)
    sigma=np.empty (len(x_data),dtype=float)
    ones.fill(1)
    i=0
    for x in sigma:
        sigma[i]=0.001
        i+=1
        
    lowerbounds=[projx*.2,0,100,100]
    upperbounds=[projx,30000, projx/2,np.inf]
    bounds=[lowerbounds,upperbounds]
    
    
    #fitting had problems converging do to the squareroot if y is the dependent residual
    #instead the constant 1 is the return value for which h,k,a,b are minimized
    #placing reasonable bounds on the parameters also helps to ensure convergence
    
    params, covariance = curve_fit(ellipse_equation, (x_data,y_data), ones, p0=initial_guess, sigma=sigma, absolute_sigma=True, bounds=bounds)#,absolute_sigma=True)
    #params, covariance = curve_fit(ellipse_equation, (x_data,y_data), ones, p0=initial_guess)#,absolute_sigma=True)
    # params, covariance = curve_fit(ellipseSq_equation, x_data, ones, p0=initial_guess, bounds=bounds)
   #data=(x_data, y_data) 
   #params, covariance = curve_fit(ellipse, data, np.ones(100), p0=initial_guess)
    
   # Extract the fitted parameters
    h, k, a, b = params
    
    #create an ellipse with upsample*imagex number of points for slicing in equal segment arcs
    step= (measuredPoints[-1,0]-measuredPoints[0,0])/(upsample*imagex)
    newx=np.arange(measuredPoints[0,0], measuredPoints[-1,0],step )
    newy=-1*b*((1-(newx-h)**2/(a**2)))**0.5+k
    #if np.amin(newy)<0:
        #newy=b*((1-(newx-h)**2/(a**2)))**0.5-k
       
    #calculater the total arc length and desired segment length (wedge)
    xdiff=np.diff(newx)
    ydiff=np.diff(newy)
    dist=(xdiff**2+ydiff**2)**0.5
    seglen=np.cumsum(dist)
    wedge=seglen[-1]/imagex
    
    #find and store the x,y locations everytime the ellipse pathdistance increases by 1 wedge distance
    start_index=0
    crossings=np.empty([0,2])
    j=0
    toadd=np.empty([1,2])
    while start_index<len(seglen) :
        for i in range(start_index, len(seglen)):
                if seglen[i] >= wedge*j:
                    toadd[0,0]=newx[i]
                    toadd[0,1]=newy[i]
                    crossings=np.concatenate((crossings,toadd),axis=0)
                    start_index= i
                    j=j+1
                else:
                   start_index=len(seglen)
    
    
    #can be useful to see data for debugging               
    print(h,k,a,b)
    print(f"Center (h, k): ({h:.2f}, {k:.2f})")
    print(f"Semi-major axis (a): {a:.2f}")
    print(f"Semi-minor axis (b): {b:.2f}")
    print(np.amin(newy))
    # Plot the data and the fitted ellipse
    plt.scatter(x_data, y_data, label="Data Points")
    #x_fit = np.linspace(min(x_data), max(x_data), 400)
    #y_fit = (1-((x_fit-h)/a)**2)**0.5*-1*b+k
    plt.plot(newx, newy, 'r', label="Fitted Ellipse")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()
    plt.title("Fitting Data Points to an Ellipse")
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
    plt.plot(newx, newy, 'r', label="Fitted Ellipse")
    plt.show()
    fitconstant=((x_data-h)/a)**2+((y_data-k)/b)**2
    print (fitconstant)
    
    return crossings, newx, newy

"""******************************************************************************************************"""
def ellipse_equation(X, h, k, a, b):
  x,y=X
  return (x-h)**2/a**2+(y-k)**2/b**2

"""******************************************************************************"""
#The following are useful functions not employed by the Main CalcWarpRempa
"""****************************************************************************"""
def remapImageFile(imageFile, remapArray, width, height, fileout):
    #width=3840
    #height=2160    
    myimage=cv2.imread(imageFile)
    warp_image = np.zeros((height,width,3), np.uint8)
    for mapdata in remapArray:
        warp_image[mapdata[1]][mapdata[0]][:]=myimage[mapdata[3]][mapdata[2]][:]
    
    #cv2.namedWindow("warped out", cv2.WINDOW_NORMAL) 
    #cv2.resizeWindow("warped out", (2560,1080))
    cv2.imwrite(fileout,warp_image)
    #cv2.imshow("warped out",warp_image)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows() 
""" *********************************************************************************"""
#folder should contain images of dimensions consist with the remap file being used (1024x768 typically)
def warpFolderImages(remapfile, folderpath, newfolder):
    myFile = pd.read_csv(remapfile, sep=',', header=None, skip_blank_lines=False)
    remap=myFile.to_numpy('int16')
    madeFolder=os.path.join(os.getcwd(),newfolder)
    os.makedirs(madeFolder)
    for filename in os.listdir(folderpath):
        print(filename)
        #hardcoded projector resolution settings for Harvard Barco 
        remapImageFile(os.path.join(folderpath, filename), remap,3840,2160, os.path.join(madeFolder, filename))
           
   