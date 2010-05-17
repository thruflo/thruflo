function (doc) {
  if (doc.parent_id) {
    emit([doc.account_id, doc.parent_id, doc.section_type, doc.mod], null);
  }
}
