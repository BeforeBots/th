
const command = document.querySelector('.commands');
const display = document.querySelect  ;

function Git(name) {
    this.name = name;
    this.lastcommitid = -1;
    this.Head = null;
    let master = new Branch("master", null);
    this.branches = []; // List of all branches.
    this.branches.push(master); // Store master branch.
}
let buildrepo = new Git("my Repo");

function commit(id,msg,parent) {
    this.id = id;
    this.msg = msg;
    this.parent = parent;
}

Git.prototype.commit = function (message) {
    let commit = new commit(++this.lastCommitId, message,this.Head);
    this.HEAD = commit;
    return commit;
};


buildrepo.commit("make your commit work");

Git.prototype.log = function() {
    let history = []; // array of commits in reverse order.
    let commit = this.HEAD.commit,
    // 1. Start from last commit
    // 2. Go back tracing to the first commit
    // 3. Push in `history`
  
    return history;
};
Git.prototype.log = function() {
    // Start from HEAD
    let commit = this.HEAD,
      history = [];
  
    while (commit) {
      history.push(commit);
      // Keep following the parent
      commit = commit.parent;
    }
  
    return history;
    // Expose Git class on window.
	window.Git = Git;
};
function Branch(name, commit) {
    this.name = name;
    this.commit = commit;
}
Git.prototype.checkout = function(branchName) {
    // Check if a branch already exists with name = branchName
     // Loop through all branches and see if we have a branch
  // called `branchName`.
  for (var i = this.branches.length; i--; ) {
    if (this.branches[i].name === branchName) {
      // We found an existing branch
      console.log("Switched to existing branch: " + branchName);
      this.HEAD = this.branches[i];
      return this;
    }
  }

  // We reach here when no matching branch is found.
     // If branch was not found, create a new one.
  var newBranch = new Branch(branchName, this.HEAD.commit);
  // Store branch.
  this.branches.push(newBranch);
  // Update HEAD
  this.HEAD = newBranch;

  console.log("Switched to new branch: " + branchName);
  return this;
};
 // instead of using integers as History replace with hashing algorithms 
  
