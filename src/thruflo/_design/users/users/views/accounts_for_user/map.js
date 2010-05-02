function (doc) {
  var i, item, doc.administrator_accounts.length;
  for (i = 0; i < l; i++) {
    item = doc.administrator_accounts[i];
    emit([doc._id, 'administrator'], item);
  }
  l = doc.member_accounts.length;
  for (i = 0; i < l; i++) {
    item = doc.member_accounts[i];
    emit([doc._id, 'administrator'], item);
  }
}