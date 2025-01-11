import os


def creat_ui_file():

    info = '''<?xml version="1.0" encoding="UTF-8"?>
        <ui version="4.0">
         <class>Anime_sharing_download</class>
         <widget class="QMainWindow" name="Anime_sharing_download">
          <property name="geometry">
           <rect>
            <x>0</x>
            <y>0</y>
            <width>404</width>
            <height>191</height>
           </rect>
          </property>
          <property name="windowTitle">
           <string>Anime_sharing_download</string>
          </property>
          <widget class="QWidget" name="centralwidget">
           <widget class="QLineEdit" name="down_path">
            <property name="geometry">
             <rect>
              <x>80</x>
              <y>10</y>
              <width>221</width>
              <height>30</height>
             </rect>
            </property>
            <property name="frame">
             <bool>true</bool>
            </property>
            <property name="alignment">
             <set>Qt::AlignmentFlag::AlignCenter</set>
            </property>
            <property name="placeholderText">
             <string>Download_PATH</string>
            </property>
           </widget>
           <widget class="QPushButton" name="user_conf_save">
            <property name="geometry">
             <rect>
              <x>310</x>
              <y>50</y>
              <width>61</width>
              <height>30</height>
             </rect>
            </property>
            <property name="text">
             <string>save</string>
            </property>
           </widget>
           <widget class="QLineEdit" name="user_name">
            <property name="geometry">
             <rect>
              <x>10</x>
              <y>50</y>
              <width>141</width>
              <height>30</height>
             </rect>
            </property>
            <property name="frame">
             <bool>true</bool>
            </property>
            <property name="alignment">
             <set>Qt::AlignmentFlag::AlignCenter</set>
            </property>
            <property name="placeholderText">
             <string>user_name</string>
            </property>
           </widget>
           <widget class="QLineEdit" name="password">
            <property name="geometry">
             <rect>
              <x>160</x>
              <y>50</y>
              <width>141</width>
              <height>30</height>
             </rect>
            </property>
            <property name="frame">
             <bool>true</bool>
            </property>
            <property name="alignment">
             <set>Qt::AlignmentFlag::AlignCenter</set>
            </property>
            <property name="placeholderText">
             <string>password</string>
            </property>
           </widget>
           <widget class="QPushButton" name="path_conf_save">
            <property name="geometry">
             <rect>
              <x>310</x>
              <y>10</y>
              <width>61</width>
              <height>30</height>
             </rect>
            </property>
            <property name="text">
             <string>save</string>
            </property>
           </widget>
           <widget class="QLineEdit" name="speed_limit">
            <property name="geometry">
             <rect>
              <x>10</x>
              <y>10</y>
              <width>61</width>
              <height>30</height>
             </rect>
            </property>
            <property name="frame">
             <bool>true</bool>
            </property>
            <property name="alignment">
             <set>Qt::AlignmentFlag::AlignCenter</set>
            </property>
            <property name="placeholderText">
             <string>speed</string>
            </property>
           </widget>
           <widget class="QPushButton" name="pushButton">
            <property name="geometry">
             <rect>
              <x>10</x>
              <y>100</y>
              <width>81</width>
              <height>31</height>
             </rect>
            </property>
            <property name="text">
             <string>start down</string>
            </property>
           </widget>
           <widget class="QPushButton" name="pushButton_2">
            <property name="geometry">
             <rect>
              <x>290</x>
              <y>100</y>
              <width>81</width>
              <height>31</height>
             </rect>
            </property>
            <property name="text">
             <string>stop down</string>
            </property>
           </widget>
          </widget>
          <widget class="QMenuBar" name="menubar">
           <property name="geometry">
            <rect>
             <x>0</x>
             <y>0</y>
             <width>404</width>
             <height>20</height>
            </rect>
           </property>
          </widget>
          <widget class="QStatusBar" name="statusbar"/>
         </widget>
         <resources/>
         <connections/>
        </ui>
        '''
    if not os.path.exists('src/UI'):
        os.makedirs('src/UI', exist_ok=True)

    with open('src/UI/index.ui', 'w', encoding='utf-8') as file:
        file.write(info)