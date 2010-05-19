function (doc) {
  emit([
      doc.owner,
      doc.name
    ],
    null
  );
}