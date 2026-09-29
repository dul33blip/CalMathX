import mongoose from 'mongoose';

const problemSchema = new mongoose.Schema(
  {
    op: { type: String, required: true },
    params: { type: Object, required: true },
    answer: { type: String },
    approx: { type: String },
    favorite: { type: Boolean, default: false },
  },
  { timestamps: true },
);

export default mongoose.model('Problem', problemSchema);
