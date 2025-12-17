# HTTP REQUEST EXAMPLES v0.1

**POST** http://127.0.0.1:9000/agent/ask

body: 
```json
{
  "device_id": "duro-1-001",
  "prompt": "Create a diagnosis screen with two labels at the top right saying Start and Stop. Name the view 'View'.",
  "context": {
            "database": {
                "settings": {
                    "persistanceUpdateTime": 1,
                    "maxDaysToLog": 10
                },
                "tags": {
                    "_NewTag": {
                        "arraydim": 1,
                        "datatype": "Number",
                        "value": 0,
                        "config": {
                        "persistent": false,
                        "historic": false,
                        "hidden": false,
                        "editable": true
                        }
                    },
                    "_NewFolder": {
                        "datatype": "Folder",
                        "arraydim": 1,
                        "config": {
                        "hidden": false,
                        "editable": true
                        },
                        "children": {
                        "_NewTag": {
                            "arraydim": 1,
                            "datatype": "Text",
                            "value": "",
                            "config": {
                                "persistent": false,
                                "historic": false,
                                "hidden": false,
                                "editable": true
                            }
                        }
                        }
                    },
                    "textTag": {
                        "arraydim": 1,
                        "datatype": "Text",
                        "value": "",
                        "config": {
                        "persistent": false,
                        "historic": false,
                        "hidden": false,
                        "editable": true
                        }
                    },
                    "textTag1": {
                        "arraydim": 1,
                        "datatype": "Text",
                        "value": "",
                        "config": {
                        "persistent": false,
                        "historic": false,
                        "hidden": false,
                        "editable": true
                        }
                    },
                    "numberTag": {
                        "arraydim": 1,
                        "datatype": "Number",
                        "value": 0,
                        "config": {
                        "persistent": false,
                        "historic": false,
                        "hidden": false,
                        "editable": true
                        }
                    },
                    "numberTag1": {
                        "arraydim": 1,
                        "datatype": "Number",
                        "value": 0,
                        "config": {
                        "persistent": false,
                        "historic": false,
                        "hidden": false,
                        "editable": true
                        }
                    },
                    "_NewTag_1": {
                        "arraydim": 1,
                        "datatype": "Number",
                        "value": 0,
                        "config": {
                        "persistent": false,
                        "historic": false,
                        "hidden": false,
                        "editable": true
                        }
                    }
                }
            },
            "modules": [],
            "hmi": {
                "views": [
                    {
                        "id": "vw_76f66be9-d58b4fa6",
                        "name": "View_1",
                        "type": "view",
                        "config": {
                        "width": 1024,
                        "height": 760,
                        "style": {},
                        "sizeMode": "normal"
                        },
                        "components": [
                        {
                            "id": "btn_c040-61a5",
                            "viewId": "",
                            "type": "button",
                            "typeAbbr": "btn_",
                            "comptName": "Button_1",
                            "visibility": true,
                            "w": 120,
                            "h": 60,
                            "y": 128.3420786306292,
                            "x": 791.2113292940138,
                            "zIndex": 0,
                            "rotationAngle": 0,
                            "sizeMode": "zoom",
                            "config": {
                                "behavior": "release",
                                "text": "Set Tag to 5",
                                "style": {
                                    "fontFamily": "Arial",
                                    "font-weight": "normal",
                                    "color": "#000000a3",
                                    "backgroundColor": "#b0b0b0",
                                    "border": "solid #000000 2px",
                                    "feedback-fx": "scale(0.9) #ff0600 1.5s",
                                    "box-shadow": "5px 5px 10px 0px #000000"
                                },
                                "placeholderType": "text"
                            },
                            "animation": {
                                "backgroundColor": "",
                                "border": "",
                                "text": "",
                                "visibility": "",
                                "color": ""
                            },
                            "events": {
                                "click": "writeTag(\"_NewTag\", 5) \n+ writeTag(\"_NewTag_1\", 20)",
                                "press": "",
                                "release": ""
                            },
                            "logic": {
                                "moduleId": "",
                                "mainTag": "",
                                "mainTagResp": ""
                            }
                        }
                        ]
                    },
                    {
                        "id": "vw_default",
                        "name": "MainView",
                        "type": "view",
                        "config": {
                        "width": 1230,
                        "height": 800,
                        "style": {
                            "fontFamily": "None",
                            "font-weight": "none",
                            "fontSize.px": 16,
                            "color": "#000000",
                            "backgroundColor": "#ffffff",
                            "borderRadius.px": 0,
                            "borderStyle": "solid",
                            "borderColor": "#00000000",
                            "borderWidth.px": 0,
                            "boxShadow": "0px 0px 0px 0px #000000"
                        },
                        "sizeMode": "zoom"
                        },
                        "components": []
                    }
                ],
                "general": {
                    "defaultViewId": "vw_76f66be9-d58b4fa6",
                    "mainView": null,
                    "mainNavBtn": false,
                    "viewsTree": [
                        {
                        "name": "MainView",
                        "type": "view",
                        "id": "vw_default"
                        },
                        {
                        "name": "View_1",
                        "type": "view",
                        "id": "vw_76f66be9-d58b4fa6"
                        }
                    ]
                }
            },
            "charts": []
  }
}
```
Response
```json 
{
    "message": "Diagnosis screen created with two labels at the top right saying Start and Stop. View named 'View'.",
    "steps": [
        {
            "title": "Create a new view",
            "details": "Create a new view with the name 'View' and set its width and height."
        },
        {
            "title": "Add two labels at the top right",
            "details": "Add two labels at the top right of the view, one with the text 'Start' and the other with the text 'Stop'."
        }
    ],
    "proposed_changes": {
        "screens": [
            {
                "id": "vw_View",
                "name": "View",
                "type": "view",
                "config": {
                    "width": 1024,
                    "height": 760,
                    "style": {},
                    "sizeMode": "normal"
                },
                "components": [
                    {
                        "id": "lbl_Start",
                        "viewId": "vw_View",
                        "type": "label",
                        "typeAbbr": "lbl_",
                        "comptName": "Label_1",
                        "visibility": true,
                        "w": 60,
                        "h": 30,
                        "y": 20,
                        "x": 920,
                        "zIndex": 0,
                        "rotationAngle": 0,
                        "sizeMode": "zoom",
                        "config": {
                            "placeholder": "Start",
                            "buttonMode": "false",
                            "style": {
                                "fontFamily": "Arial",
                                "font-weight": "normal",
                                "color": "#000000",
                                "backgroundColor": "#b0b0b0",
                                "border": "solid #000000 2px"
                            }
                        },
                        "animation": {
                            "backgroundColor": "",
                            "border": "",
                            "text": "",
                            "visibility": "",
                            "color": ""
                        },
                        "events": {
                            "click": ""
                        }
                    },
                    {
                        "id": "lbl_Stop",
                        "viewId": "vw_View",
                        "type": "label",
                        "typeAbbr": "lbl_",
                        "comptName": "Label_2",
                        "visibility": true,
                        "w": 60,
                        "h": 30,
                        "y": 60,
                        "x": 920,
                        "zIndex": 0,
                        "rotationAngle": 0,
                        "sizeMode": "zoom",
                        "config": {
                            "placeholder": "Stop",
                            "buttonMode": "false",
                            "style": {
                                "fontFamily": "Arial",
                                "font-weight": "normal",
                                "color": "#000000",
                                "backgroundColor": "#b0b0b0",
                                "border": "solid #000000 2px"
                            }
                        },
                        "animation": {
                            "backgroundColor": "",
                            "border": "",
                            "text": "",
                            "visibility": "",
                            "color": ""
                        },
                        "events": {
                            "click": ""
                        }
                    }
                ]
            }
        ]
    }
}
```
