function (doc) {
  var k = [doc.username, doc.password];
  emit(k, doc._id);
  k[0] = doc.email_address;
  emit(k, doc._id);
}