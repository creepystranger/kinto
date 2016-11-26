import React from "react";
import ReactDOM from "react-dom";
import KintoAdmin from "kinto-admin";
import * as signoffPlugin from "kinto-admin/lib/plugins/signoff";


const settings = {
  maxPerPage: 50,
  authMethods: ['basicauth']
};


ReactDOM.render(
  <KintoAdmin settings={settings} plugins={[signoffPlugin]}/>,
  document.getElementById("root")
);
