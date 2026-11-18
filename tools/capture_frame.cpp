// Screenshot helper (not part of the assignment code).
// It includes a scene file unchanged, and when the scene calls glFlush()
// the frame is read back with glReadPixels and saved as a PPM image.
// Build with -DSCENE_FILE='"path/to/scene.cpp"' and run with SHOT=out.ppm
#ifdef __APPLE__
#include <GLUT/glut.h>
#else
#include <GL/glut.h>
#endif
#include <cstdio>
#include <cstdlib>
#include <vector>

static void saveFrameAndExit()
{
    glFinish();
    int w = glutGet(GLUT_WINDOW_WIDTH);
    int h = glutGet(GLUT_WINDOW_HEIGHT);
    std::vector<unsigned char> pixels(w * h * 3);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, pixels.data());

    const char *path = getenv("SHOT") ? getenv("SHOT") : "frame.ppm";
    FILE *f = fopen(path, "wb");
    fprintf(f, "P6\n%d %d\n255\n", w, h);
    for (int y = h - 1; y >= 0; y--)            // OpenGL rows start at the bottom
        fwrite(&pixels[y * w * 3], 1, w * 3, f);
    fclose(f);
    exit(0);
}

#define glFlush() do { glFlush(); saveFrameAndExit(); } while (0)
#define main scene_main
#include SCENE_FILE
#undef main
#undef glFlush

int main(int argc, char **argv) { return scene_main(argc, argv); }
