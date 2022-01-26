const { MongoClient } = require("mongodb");
function conn_string() {
  MONGODB_URI = process.env.MONGODB_URI
  MONGODB_PASSWORD = process.env.MONGODB_PASSWORD
  MONGODB_USER = process.env.MONGODB_USER
  DATABASE_NAME = process.env.DATABASE_NAME

//  │ mongodb+srv://opta-mernbackend-mongod.dmw9f.mongodb.net undefined undefined myFirstDatabase                                                                                 │

  console.log(MONGODB_URI, MONGODB_USER, MONGODB_PASSWORD, DATABASE_NAME)
  parts = MONGODB_URI.split("//")
  if (DATABASE_NAME != "") {
    rtn_str = [
      parts[0], 
      MONGODB_USER + ":" + MONGODB_PASSWORD + "@" + parts[1] + "/" + DATABASE_NAME + + "?retryWrites=true&w=majority" 
    ].join("//")
  }
  else {
    rtn_str = [
      parts[0],
      MONGODB_USER + ":" + MONGODB_PASSWORD + "@" + parts[1]
  ].join("//")
  }
  console.log(rtn_str)
  return rtn_str

}
const Db = conn_string();
const client = new MongoClient(Db, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});
 
var _db;
 
module.exports = {
  connectToServer: function (callback) {
    client.connect(function (err, db) {
      // Verify we got a good "db" object
      if (db)
      {
        _db = db.db("myFirstDatabase");
        console.log("Successfully connected to MongoDB."); 
      }
      return callback(err);
         });
  },
 
  getDb: function () {
    return _db;
  },
};

