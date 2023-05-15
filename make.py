import os
import shutil

if __name__ == '__main__':
    for file in sorted(os.listdir('dist/js')):
        if file.startswith('app'):
            js_app = file
        elif file.startswith('chunk'):
            js_chunk = file
    for file in sorted(os.listdir('dist/css')):
        if file.startswith('app'):
            css_app = file
        elif file.startswith('chunk'):
            css_chunk = file
    context = f"""<RCC>
    <qresource>
        <file alias="index.html">dist/all.html</file>
        <file alias="app.js">dist/js/{js_app}</file>
        <file alias="chunk.js">dist/js/{js_chunk}</file>
        <file alias="app.css">dist/css/{css_app}</file>
        <file alias="chunk.css">dist/css/{css_chunk}</file>
    </qresource>
</RCC>
"""
    with open('mpr.qrc', 'w') as f:
        f.write(context)
    shutil.copy('all.html', 'dist/all.html')
    os.system('D:/Qt/Qt5.14.2/5.14.2/msvc2017_64/bin/rcc.exe -binary mpr.qrc -o mpr.rcc')
