#include <stdio.h>
#include <math.h>

// C version of the Barycentric triangle check

// gcc -O3 -shared -o libCextesions.so -fPIC Cextesions.c

int sign(int Tri[6]);
int pointInTriangle(int Pnts[8]);
int rectInsideQuadrilateral(int Quad[8], int Rect[8]);


// Function for finding the side of the point from edge
int sign(int Tri[6])
{
    return (Tri[0] - Tri[4]) * (Tri[3] - Tri[5]) - (Tri[2] - Tri[4]) * (Tri[1] - Tri[5]);
}

// Function for checking point inside triangle
int pointInTriangle(int Pnts[8])
{
    int t1 = (sign((int [6]){Pnts[0], Pnts[1], Pnts[2], Pnts[3], Pnts[4], Pnts[5]}) < 0) ? 1: 0;
    int t2 = (sign((int [6]){Pnts[0], Pnts[1], Pnts[4], Pnts[5], Pnts[6], Pnts[7]}) < 0) ? 1: 0;
    int t3 = (sign((int [6]){Pnts[0], Pnts[1], Pnts[6], Pnts[7], Pnts[2], Pnts[3]}) < 0) ? 1: 0;

    return (t1 == t2) && (t2 == t3);
}

// Function for checking if rect is inside 4 sided polygon(Quadrilateral )
int rectInsideQuadrilateral(int Quad[8], int Rect[8])
{
    int index = 0;
    int cnt = 0;
    for (cnt; cnt < 4; cnt++)
    {
        index = cnt << 1;
        // The quadri is separated in to 2 triangles
        if (pointInTriangle((int [8]){Rect[index], Rect[index+1], Quad[0], Quad[1], Quad[2], Quad[3], Quad[6], Quad[7]}) ||
            pointInTriangle((int [8]){Rect[index], Rect[index+1], Quad[6], Quad[7], Quad[2], Quad[3], Quad[4], Quad[5]})){continue;}
        else{return 0;}
    }
    // All points inside!
    return 1;
}

