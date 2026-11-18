/*
 * ==========================================================================
 *  Computer Graphics - Mid Term Lab Assignment
 *  Problem 1 : Bangladesh Tribute Scene
 *              (DDA Line, Bresenham Line, Midpoint Circle)
 * ==========================================================================
 *  The only OpenGL drawing call used is putPixel() -> a single GL_POINT.
 *  Every line and every circle is made by our own algorithms below.
 *
 *  Label of every part (which algorithm draws what):
 *    DDA       : flagpole, grille bars inside the pillars, decorative line
 *                on the platform, flower stems and leaves
 *    Bresenham : flag frame, platform border, pillar edges, footpath edges
 *                and tile lines, and every filled area (horizontal scan-lines)
 *    Midpoint  : red sun of the flag, big red sun behind the Minar, arch on
 *                top of the middle pillar, knob of the flagpole, clouds,
 *                flower petals
 *
 *  Part C (extra elements): Road/Footpath, Clouds, Flowers
 *
 *  While drawing the first frame the program prints the first 5 plotted
 *  points of some algorithm runs in the console (used in the report).
 *
 *  Compile:
 *    Windows (Code::Blocks / MinGW) : -lfreeglut -lopengl32 -lglu32
 *    Linux                          : g++ bangladesh_tribute_scene.cpp -lGL -lGLU -lglut
 *    macOS                          : clang++ bangladesh_tribute_scene.cpp -framework OpenGL -framework GLUT
 * ==========================================================================
 */

#ifdef _WIN32
#include <windows.h>
#endif
#ifdef __APPLE__
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif
#include <cstdio>
#include <cstdlib>
#include <cmath>

// ------------------------- window and scene settings ----------------------
const int WIDTH  = 1000;
const int HEIGHT = 600;
const int GROUND = 230;        // y of the horizon (top of the grass field)

// ------------------- console log of the first plotted points ---------------
const int LOG_DDA = 1, LOG_BRESENHAM = 2, LOG_CIRCLE = 3;
int  logAlgo    = 0;           // algorithm that should print now (0 = none)
int  logLeft    = 0;           // how many points are still to be printed
bool firstFrame = true;        // print only while drawing the first frame

void startLog(int algo, const char *title)
{
    if (!firstFrame) return;
    logAlgo = algo;
    logLeft = 5;                       // first 5 plotted points
    printf("\n%s\n", title);
}

bool shouldLog(int algo)
{
    if (logAlgo != algo || logLeft <= 0) return false;
    logLeft--;
    return true;
}

// ------------------------------ basic pixel --------------------------------
void setColor(int r, int g, int b)
{
    glColor3ub(r, g, b);
}

void putPixel(int x, int y)
{
    glBegin(GL_POINTS);
    glVertex2i(x, y);
    glEnd();
}

// =========================== 1. DDA line algorithm =========================
void ddaLine(int x1, int y1, int x2, int y2)
{
    int dx = x2 - x1;
    int dy = y2 - y1;
    int steps = abs(dx) > abs(dy) ? abs(dx) : abs(dy);

    if (steps == 0) {                  // start and end are the same pixel
        putPixel(x1, y1);
        return;
    }

    float xInc = dx / (float)steps;
    float yInc = dy / (float)steps;
    float x = x1, y = y1;

    for (int k = 0; k <= steps; k++) {
        int px = (int)floor(x + 0.5f); // round to the nearest pixel
        int py = (int)floor(y + 0.5f);
        putPixel(px, py);
        if (shouldLog(LOG_DDA))
            printf("  k=%d  x=%.2f  y=%.2f  -> pixel (%d, %d)\n", k, x, y, px, py);
        x += xInc;
        y += yInc;
    }
}

// ======================== 2. Bresenham line algorithm ======================
// Works for every slope: it steps along x when the line is gentle (|m| <= 1)
// and along y when the line is steep (|m| > 1).
void bresenhamLine(int x1, int y1, int x2, int y2)
{
    int dx = abs(x2 - x1);
    int dy = abs(y2 - y1);
    int sx = (x2 >= x1) ? 1 : -1;
    int sy = (y2 >= y1) ? 1 : -1;
    int x = x1, y = y1;

    if (dx >= dy) {                    // gentle slope
        int p = 2 * dy - dx;
        for (int k = 0; k <= dx; k++) {
            putPixel(x, y);
            if (shouldLog(LOG_BRESENHAM))
                printf("  k=%d  p=%d  -> pixel (%d, %d)\n", k, p, x, y);
            x += sx;
            if (p >= 0) { y += sy; p += 2 * dy - 2 * dx; }
            else        {          p += 2 * dy; }
        }
    } else {                           // steep slope
        int p = 2 * dx - dy;
        for (int k = 0; k <= dy; k++) {
            putPixel(x, y);
            if (shouldLog(LOG_BRESENHAM))
                printf("  k=%d  p=%d  -> pixel (%d, %d)\n", k, p, x, y);
            y += sy;
            if (p >= 0) { x += sx; p += 2 * dx - 2 * dy; }
            else        {          p += 2 * dx; }
        }
    }
}

// ======================= 3. Midpoint circle algorithm ======================
// Every step finds one point (x, y) of the first octant, the other 7 points
// come from symmetry. "upperHalf" keeps only the top half (used for arcs)
// and "filled" joins the symmetric points with Bresenham scan-lines.
void circlePoints(int xc, int yc, int x, int y, bool filled, bool upperHalf)
{
    if (filled) {
        bresenhamLine(xc - x, yc + y, xc + x, yc + y);
        bresenhamLine(xc - y, yc + x, xc + y, yc + x);
        if (!upperHalf) {
            bresenhamLine(xc - x, yc - y, xc + x, yc - y);
            bresenhamLine(xc - y, yc - x, xc + y, yc - x);
        }
    } else {
        putPixel(xc + x, yc + y);   putPixel(xc - x, yc + y);
        putPixel(xc + y, yc + x);   putPixel(xc - y, yc + x);
        if (!upperHalf) {
            putPixel(xc + x, yc - y);   putPixel(xc - x, yc - y);
            putPixel(xc + y, yc - x);   putPixel(xc - y, yc - x);
        }
    }
}

void midpointCircle(int xc, int yc, int r, bool filled, bool upperHalf)
{
    int x = 0, y = r;
    int p = 1 - r;                     // initial decision parameter
    int k = 0;

    while (x <= y) {
        circlePoints(xc, yc, x, y, filled, upperHalf);
        if (shouldLog(LOG_CIRCLE))
            printf("  k=%d  (x=%d, y=%d)  p=%d  -> pixel (%d, %d)\n",
                   k, x, y, p, xc + x, yc + y);
        x++;
        if (p < 0) p += 2 * x + 1;
        else     { y--; p += 2 * (x - y) + 1; }
        k++;
    }
}

void drawCircle(int xc, int yc, int r)     { midpointCircle(xc, yc, r, false, false); }
void fillCircle(int xc, int yc, int r)     { midpointCircle(xc, yc, r, true,  false); }
void drawArc(int xc, int yc, int r)        { midpointCircle(xc, yc, r, false, true);  }
void fillHalfCircle(int xc, int yc, int r) { midpointCircle(xc, yc, r, true,  true);  }

// --------------------------- rectangle helpers -----------------------------
// (x1, y1) = bottom-left corner, (x2, y2) = top-right corner

void drawRect(int x1, int y1, int x2, int y2)     // border, Bresenham
{
    bresenhamLine(x1, y1, x2, y1);     // bottom
    bresenhamLine(x2, y1, x2, y2);     // right
    bresenhamLine(x2, y2, x1, y2);     // top
    bresenhamLine(x1, y2, x1, y1);     // left
}

void fillRect(int x1, int y1, int x2, int y2)     // one scan-line per row
{
    for (int y = y1; y <= y2; y++)
        bresenhamLine(x1, y, x2, y);
}

// ================================ SCENE ====================================

// Grass field below the horizon (the sky is the clear colour)
void drawGround()
{
    setColor(86, 160, 40);
    fillRect(0, 0, WIDTH - 1, GROUND);
}

// ----------------------- Part A : Bangladesh flag --------------------------
// Real flag proportions: length : height = 10 : 6, sun radius = length / 5,
// sun centre at 9/20 of the length (slightly left of centre).
void drawFlag(int poleX, int poleBottom, int poleTop, int flagLength)
{
    int poleWidth  = 4;
    int flagHeight = flagLength * 6 / 10;
    int left   = poleX + poleWidth;
    int right  = left + flagLength;
    int top    = poleTop - 8;
    int bottom = top - flagHeight;

    int sunR = flagLength / 5;
    int sunX = left + flagLength * 9 / 20;
    int sunY = bottom + flagHeight / 2;

    // stand of the pole (Bresenham)
    setColor(120, 120, 120);
    fillRect(poleX - 10, poleBottom - 8, poleX + poleWidth + 10, poleBottom);

    // flagpole: parallel DDA lines make a thick pole
    setColor(70, 70, 70);
    startLog(LOG_DDA, "DDA - Flagpole");
    for (int i = 0; i < poleWidth; i++)
        ddaLine(poleX + i, poleBottom, poleX + i, poleTop);

    // golden knob on top of the pole (Midpoint)
    setColor(218, 165, 32);
    fillCircle(poleX + poleWidth / 2, poleTop + 5, 5);

    // green body of the flag (Bresenham scan-lines)
    setColor(0, 106, 78);
    fillRect(left, bottom, right, top);

    // red sun (Midpoint)
    setColor(244, 42, 65);
    fillCircle(sunX, sunY, sunR);
    startLog(LOG_CIRCLE, "Midpoint Circle - Red sun of the flag");
    drawCircle(sunX, sunY, sunR);

    // flag frame / border (Bresenham)
    setColor(0, 50, 35);
    startLog(LOG_BRESENHAM, "Bresenham - Flag frame (bottom edge)");
    drawRect(left, bottom, right, top);
}

// ----------------------- Part B : Shaheed Minar ----------------------------
// One pillar = white frame (Bresenham) + black grille bars (DDA)
void drawPillar(int centerX, int baseY, int width, int height)
{
    int left  = centerX - width / 2;
    int right = centerX + width / 2;
    int top   = baseY + height;
    int frame = 6;                         // thickness of the white frame

    setColor(248, 248, 248);
    fillRect(left, baseY, left + frame, top);          // left side
    fillRect(right - frame, baseY, right, top);        // right side
    fillRect(left, top - frame, right, top);           // top side
    fillRect(left, baseY, right, baseY + frame);       // bottom side

    setColor(25, 25, 25);                              // grille bars (DDA)
    for (int x = left + frame + 3; x < right - frame; x += 5)
        ddaLine(x, baseY + frame, x, top - frame);

    setColor(110, 110, 110);                           // pillar edges
    drawRect(left, baseY, right, top);                 // (Bresenham)
}

void drawShaheedMinar(int cx, int baseY)
{
    int platformHalf = 230;
    int platformTop  = baseY + 25;
    int tallest      = 250;                // height of the middle pillar
    int spacing      = 80;                 // distance between pillars
    int middleWidth  = 50;
    int sideWidth    = 36;

    // big red sun behind the pillars (Midpoint, filled)
    setColor(215, 25, 45);
    fillCircle(cx, platformTop + tallest / 2 + 20, 110);

    // base platform: one wide rectangle
    setColor(205, 205, 205);
    fillRect(cx - platformHalf, baseY, cx + platformHalf, platformTop);
    setColor(90, 90, 90);
    drawRect(cx - platformHalf, baseY, cx + platformHalf, platformTop);       // Bresenham
    ddaLine(cx - platformHalf, baseY + 12, cx + platformHalf, baseY + 12);    // DDA decoration

    // five pillars: the middle one is the tallest, the others get shorter
    for (int k = -2; k <= 2; k++) {
        int height = tallest - abs(k) * 55;
        int width  = (k == 0) ? middleWidth : sideWidth;
        drawPillar(cx + k * spacing, platformTop, width, height);
    }

    // arch on top of the middle pillar (Midpoint, upper half only)
    int archY = platformTop + tallest;
    int archR = middleWidth / 2;
    setColor(248, 248, 248);
    fillHalfCircle(cx, archY, archR);
    setColor(110, 110, 110);
    startLog(LOG_CIRCLE, "Midpoint Circle - Arch on the middle pillar");
    drawArc(cx, archY, archR);
}

// ------------------ Part C-1 : Footpath in front (Bresenham) ---------------
// The path is wide at the bottom and narrow at the Minar (perspective).
int pathHalfWidth(int y, int topY, int topHalf, int bottomHalf)
{
    return bottomHalf + (topHalf - bottomHalf) * y / topY;
}

void drawFootpath(int cx, int topY, int topHalf, int bottomHalf)
{
    setColor(196, 176, 140);                           // path surface
    for (int y = 0; y <= topY; y++) {
        int half = pathHalfWidth(y, topY, topHalf, bottomHalf);
        bresenhamLine(cx - half, y, cx + half, y);
    }

    setColor(150, 128, 95);                            // tile lines
    for (int y = 25; y < topY; y += 25) {
        int half = pathHalfWidth(y, topY, topHalf, bottomHalf);
        bresenhamLine(cx - half, y, cx + half, y);
    }

    setColor(90, 70, 45);                              // two side edges
    startLog(LOG_BRESENHAM, "Bresenham - Footpath left edge");
    bresenhamLine(cx - bottomHalf, 0, cx - topHalf, topY);
    bresenhamLine(cx + bottomHalf, 0, cx + topHalf, topY);
}

// ------------- Part C-2 : Clouds = overlapping circles (Midpoint) ----------
void drawCloud(int x, int y, int r)
{
    setColor(255, 255, 255);
    fillCircle(x - r, y, r * 3 / 4);
    fillCircle(x, y + r / 3, r);
    fillCircle(x + r, y, r * 3 / 4);
    fillCircle(x + r / 2, y - r / 4, r * 2 / 3);
}

// ---------- Part C-3 : Flowers = small circles (Midpoint) + stem (DDA) -----
void drawFlower(int x, int y, int stemHeight, int lean, int r, int g, int b)
{
    int headX = x + lean;
    int headY = y + stemHeight;
    int midX  = x + lean / 2;
    int midY  = y + stemHeight / 2;
    int petal = 5;

    setColor(30, 110, 30);
    ddaLine(x, y, headX, headY);                       // stem (DDA)
    ddaLine(midX, midY, midX + 9, midY + 6);           // leaf (DDA)
    ddaLine(midX, midY, midX - 9, midY + 6);           // leaf (DDA)

    setColor(r, g, b);                                 // petals (Midpoint)
    fillCircle(headX - petal, headY, petal);
    fillCircle(headX + petal, headY, petal);
    fillCircle(headX, headY - petal, petal);
    fillCircle(headX, headY + petal, petal);

    setColor(255, 210, 0);                             // centre (Midpoint)
    fillCircle(headX, headY, 3);
}

// =============================== display ===================================
void display()
{
    glClear(GL_COLOR_BUFFER_BIT);
    if (firstFrame)
        printf("First 5 plotted points of some algorithm runs\n");

    int minarX = 640;                  // centre of the Shaheed Minar
    int minarY = 170;                  // bottom of its platform

    drawGround();

    // Part C-2 : clouds
    drawCloud(330, 540, 26);
    drawCloud(520, 565, 20);
    drawCloud(890, 530, 30);

    // Part C-1 : footpath (drawn first so the platform covers its top)
    drawFootpath(minarX, minarY, 70, 170);

    // Part B : Shaheed Minar
    drawShaheedMinar(minarX, minarY);

    // Part C-3 : flowers on both sides of the footpath
    for (int i = 0; i < 5; i++) {
        int offset = 190 + i * 34;
        int baseY  = 55 + (i % 2) * 22;
        int lean   = (i % 2 == 0) ? 6 : -6;
        if (i == 0) startLog(LOG_DDA, "DDA - Flower stem");
        drawFlower(minarX - offset, baseY, 40, lean, 220, 20, 60);   // red
        drawFlower(minarX + offset, baseY, 40, -lean, 255, 255, 255); // white
    }

    // Part A : Bangladesh flag on its pole
    drawFlag(110, 140, 500, 200);

    glFlush();
    firstFrame = false;
}

void init()
{
    glClearColor(0.53f, 0.81f, 0.98f, 1.0f);           // sky blue
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluOrtho2D(0, WIDTH, 0, HEIGHT);                   // 1 unit = 1 pixel
    glPointSize(1.0f);
}

int main(int argc, char **argv)
{
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB);
    glutInitWindowSize(WIDTH, HEIGHT);
    glutInitWindowPosition(100, 50);
    glutCreateWindow("Bangladesh Tribute Scene - DDA, Bresenham, Midpoint Circle");
    init();
    glutDisplayFunc(display);
    glutMainLoop();
    return 0;
}
