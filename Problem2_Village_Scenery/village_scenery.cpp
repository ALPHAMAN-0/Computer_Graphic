/*
 * ==========================================================================
 *  Computer Graphics - Mid Term Lab Assignment
 *  Problem 2 : Simple Village Scenery (OpenGL built-in functions)
 * ==========================================================================
 *  OpenGL primitives used:
 *    GL_QUADS     : sky, ground, river, house bodies, doors, windows, trunk
 *    GL_TRIANGLES : roofs, mountains and snow caps, boat sail
 *    GL_POLYGON   : sun, clouds, tree leaves, boat hull
 *    GL_LINES     : window bars, river waves, boat mast, birds
 *
 *  Part C (extra elements): Mountains, Boat on the river, Birds
 *
 *  Scene arrangement: gluOrtho2D(0, 1000, 0, 600), so 1 unit = 1 pixel.
 *  Every object is drawn around its own origin (0, 0), then it is moved
 *  to its place with glTranslatef() and resized with glScalef().
 *
 *  Compile:
 *    Windows (Code::Blocks / MinGW) : -lfreeglut -lopengl32 -lglu32
 *    Linux                          : g++ village_scenery.cpp -lGL -lGLU -lglut
 *    macOS                          : clang++ village_scenery.cpp -framework OpenGL -framework GLUT
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
#include <cmath>

const int   WIDTH   = 1000;
const int   HEIGHT  = 600;
const float HORIZON = 330;               // sky is above, ground is below
const float PI      = 3.14159265f;

struct Color { float r, g, b; };

void setColor(Color c) { glColor3f(c.r, c.g, c.b); }

// --------------------------- basic shapes -----------------------------------
void quad(float x, float y, float w, float h)                      // GL_QUADS
{
    glBegin(GL_QUADS);
    glVertex2f(x, y);
    glVertex2f(x + w, y);
    glVertex2f(x + w, y + h);
    glVertex2f(x, y + h);
    glEnd();
}

void triangle(float x1, float y1, float x2, float y2, float x3, float y3)  // GL_TRIANGLES
{
    glBegin(GL_TRIANGLES);
    glVertex2f(x1, y1);
    glVertex2f(x2, y2);
    glVertex2f(x3, y3);
    glEnd();
}

void circle(float cx, float cy, float r)                           // GL_POLYGON
{
    glBegin(GL_POLYGON);
    for (int i = 0; i < 60; i++) {
        float angle = 2 * PI * i / 60;
        glVertex2f(cx + r * cos(angle), cy + r * sin(angle));
    }
    glEnd();
}

void line(float x1, float y1, float x2, float y2)                  // GL_LINES
{
    glBegin(GL_LINES);
    glVertex2f(x1, y1);
    glVertex2f(x2, y2);
    glEnd();
}

// ======================= Part A : Background ===============================
void drawSky()
{
    glBegin(GL_QUADS);                   // one big rectangle, darker at the top
    glColor3f(0.75f, 0.90f, 1.00f);
    glVertex2f(0, HORIZON);
    glVertex2f(WIDTH, HORIZON);
    glColor3f(0.35f, 0.65f, 0.95f);
    glVertex2f(WIDTH, HEIGHT);
    glVertex2f(0, HEIGHT);
    glEnd();
}

void drawGround()
{
    glColor3f(0.35f, 0.72f, 0.25f);
    quad(0, 0, WIDTH, HORIZON);
}

void drawSun(float x, float y, float r)
{
    glColor3f(1.0f, 0.85f, 0.10f);
    circle(x, y, r);
}

void drawCloud(float x, float y, float s)
{
    glPushMatrix();
    glTranslatef(x, y, 0);
    glScalef(s, s, 1);
    glColor3f(1.0f, 1.0f, 1.0f);
    circle(-30, 0, 22);
    circle(0, 10, 30);
    circle(32, 0, 22);
    circle(5, -10, 22);
    glPopMatrix();
}

// ======================= Part B : Village ==================================
// House drawn at origin: body 100 x 70, roof on top, door and two windows
void drawHouse(float x, float y, float s, Color wall, Color roof)
{
    glPushMatrix();
    glTranslatef(x, y, 0);
    glScalef(s, s, 1);

    setColor(wall);                              // body
    quad(0, 0, 100, 70);

    setColor(roof);                              // roof
    triangle(-12, 70, 50, 115, 112, 70);

    glColor3f(0.40f, 0.22f, 0.10f);              // door
    quad(40, 0, 20, 40);

    glColor3f(0.60f, 0.85f, 1.00f);              // windows
    quad(12, 32, 18, 18);
    quad(70, 32, 18, 18);

    glColor3f(0.20f, 0.20f, 0.20f);              // window bars
    line(21, 32, 21, 50);   line(12, 41, 30, 41);
    line(79, 32, 79, 50);   line(70, 41, 88, 41);

    glPopMatrix();
}

void drawTree(float x, float y, float s)
{
    glPushMatrix();
    glTranslatef(x, y, 0);
    glScalef(s, s, 1);

    glColor3f(0.45f, 0.27f, 0.10f);              // trunk
    quad(-8, 0, 16, 75);

    glColor3f(0.10f, 0.50f, 0.15f);              // leaves (circle cluster)
    circle(-25, 85, 28);
    circle(25, 85, 28);
    circle(0, 110, 32);
    circle(0, 80, 25);

    glPopMatrix();
}

void drawRiver()
{
    glColor3f(0.20f, 0.50f, 0.85f);              // long quad across the scene
    glBegin(GL_QUADS);
    glVertex2f(0, 40);
    glVertex2f(WIDTH, 70);
    glVertex2f(WIDTH, 160);
    glVertex2f(0, 130);
    glEnd();

    glColor3f(0.75f, 0.90f, 1.00f);              // small waves
    for (int x = 30; x < WIDTH; x += 90) {
        float y = 65 + x * 0.03f;                // follow the river slope
        line(x, y, x + 30, y + 1);
        line(x + 45, y + 32, x + 75, y + 33);
    }
}

// ======================= Part C : Extra elements ===========================
void drawMountain(float x, float w, float h, Color c)
{
    setColor(c);
    triangle(x, HORIZON, x + w / 2, HORIZON + h, x + w, HORIZON);

    glColor3f(1.0f, 1.0f, 1.0f);                 // snow cap = top 20 %
    triangle(x + w * 0.4f, HORIZON + h * 0.8f,
             x + w / 2,    HORIZON + h,
             x + w * 0.6f, HORIZON + h * 0.8f);
}

void drawBoat(float x, float y, float s)
{
    glPushMatrix();
    glTranslatef(x, y, 0);
    glScalef(s, s, 1);

    glColor3f(0.45f, 0.25f, 0.10f);              // hull
    glBegin(GL_POLYGON);
    glVertex2f(-42, 0);
    glVertex2f(42, 0);
    glVertex2f(60, 18);
    glVertex2f(-60, 18);
    glEnd();

    glColor3f(0.15f, 0.15f, 0.15f);              // mast
    line(0, 18, 0, 90);

    glColor3f(1.0f, 0.97f, 0.88f);               // sail
    triangle(3, 85, 3, 25, 48, 25);

    glPopMatrix();
}

void drawBird(float x, float y, float s)
{
    glPushMatrix();
    glTranslatef(x, y, 0);
    glScalef(s, s, 1);
    glColor3f(0.10f, 0.10f, 0.10f);
    line(-12, 8, 0, 0);                          // left wing
    line(0, 0, 12, 8);                           // right wing  -> V shape
    glPopMatrix();
}

// =============================== display ===================================
void display()
{
    glClear(GL_COLOR_BUFFER_BIT);

    // ---- Part A : background ----
    drawSky();
    drawSun(840, 515, 42);

    Color farHill  = {0.45f, 0.45f, 0.60f};
    Color nearHill = {0.36f, 0.38f, 0.52f};
    drawMountain(-80, 360, 150, farHill);        // Part C : mountains
    drawMountain(200, 400, 185, nearHill);
    drawMountain(520, 330, 135, farHill);
    drawMountain(760, 360, 165, nearHill);

    drawCloud(150, 520, 1.0f);
    drawCloud(430, 550, 0.8f);
    drawCloud(650, 505, 1.1f);

    drawGround();

    // ---- Part B : village ----
    drawRiver();

    Color wall1 = {0.96f, 0.86f, 0.60f}, roof1 = {0.70f, 0.15f, 0.12f};
    Color wall2 = {0.90f, 0.75f, 0.55f}, roof2 = {0.55f, 0.30f, 0.15f};
    drawHouse(90, 195, 1.6f, wall1, roof1);      // big house (near)
    drawHouse(380, 200, 1.3f, wall2, roof2);     // small house
    drawTree(720, 195, 1.2f);

    // ---- Part C : boat and birds ----
    drawBoat(600, 85, 1.0f);

    for (int i = 0; i < 5; i++)                  // a group of birds
        drawBird(500 + i * 40, 450 + (i % 2) * 18, 1.0f);

    glFlush();
}

void init()
{
    glClearColor(1.0f, 1.0f, 1.0f, 1.0f);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluOrtho2D(0, WIDTH, 0, HEIGHT);             // 1 unit = 1 pixel
    glMatrixMode(GL_MODELVIEW);
    glLineWidth(2.0f);
}

int main(int argc, char **argv)
{
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB);
    glutInitWindowSize(WIDTH, HEIGHT);
    glutInitWindowPosition(100, 50);
    glutCreateWindow("Simple Village Scenery - OpenGL");
    init();
    glutDisplayFunc(display);
    glutMainLoop();
    return 0;
}
