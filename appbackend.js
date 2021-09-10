document.getElementById("querybutton").addEventListener("click", function () {
  let val = document.getElementById("shellquery").value;
  console.log("input value -> ", val);
  let port_no = window.location.host.split(":")[1];
  let url = "http://localhost:".concat(port_no, " ");
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json;charset=utf-8",
    },
    body: JSON.stringify(val),
  })
    .then((response) => response.text())
    .then((resp) => console.log(resp));
});
